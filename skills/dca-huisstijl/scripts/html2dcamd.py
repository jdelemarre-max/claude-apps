#!/usr/bin/env python3
"""
html2dcamd.py — zet een handgebouwd DCA-huisstijl-HTML-document terug om
naar de markdown-subset van dca_document.py.

Bedoeld om oudere, met de hand geschreven documenten alsnog een bron te
geven, zodat elke volgende versie een edit is in plaats van een herbouw.

    python html2dcamd.py acc.html > acc.src.md
    python dca_document.py --type pdf --titel "" --in acc.src.md --out acc.pdf

Herkent: h1 (→ titel), p.sub (→ sub), h2/h3, p, ul/ol, table,
div.kern / div.box / div.cta, table.two (→ ::: cols), class="pb"
(→ <!--pb-->), span.ru (→ **vet**), span.end (→ ==goud==),
p.foot (weggelaten; het script zet de footer zelf).

Beperkingen — bewust, en zichtbaar in de output:
- rowspan/colspan worden platgeslagen; herhaalde cellen worden leeg gelaten.
- Inline style-attributen op losse cellen gaan verloren.
Controleer de eerste render dus visueel voordat je het origineel weggooit.
"""
import re
import sys
from html.parser import HTMLParser
import html as _h


def clean(t):
    t = re.sub(r"\s+", " ", t)
    return t.strip()


class Node:
    def __init__(self, tag, attrs=None):
        self.tag = tag
        self.attrs = dict(attrs or {})
        self.kids = []
        self.text = ""

    def cls(self):
        return self.attrs.get("class", "")


class Tree(HTMLParser):
    VOID = {"br", "hr", "img", "meta", "link", "input"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs)
        self.stack[-1].kids.append(n)
        if tag not in self.VOID:
            self.stack.append(n)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, d):
        if d.strip():
            n = Node("#text")
            n.text = d
            self.stack[-1].kids.append(n)


def inline_of(node):
    """Node-inhoud → inline markdown."""
    out = []
    for k in node.kids:
        if k.tag == "#text":
            out.append(k.text)
        elif k.tag in ("b", "strong"):
            out.append("**" + clean(inline_of(k)) + "**")
        elif k.tag in ("i", "em"):
            out.append("*" + clean(inline_of(k)) + "*")
        elif k.tag == "code":
            out.append("`" + clean(inline_of(k)) + "`")
        elif k.tag == "br":
            out.append(" · ")
        elif k.tag == "a":
            out.append(f"[{clean(inline_of(k))}]({k.attrs.get('href', '')})")
        elif k.tag == "span":
            c = k.cls()
            inner = clean(inline_of(k))
            if not inner:
                continue
            if "end" in c:
                out.append("==" + inner + "==")
            elif "ru" in c:
                out.append("**" + inner + "**")
            else:
                out.append(inner)
        else:
            out.append(inline_of(k))
    return "".join(out)


def cells_of(tr):
    return [k for k in tr.kids if k.tag in ("td", "th")]


def rows_of(tbl):
    rows = []
    for k in tbl.kids:
        if k.tag == "tr":
            rows.append(k)
        elif k.tag in ("thead", "tbody", "tfoot"):
            rows.extend(x for x in k.kids if x.tag == "tr")
    return rows


def table_md(tbl, out):
    """Zet een HTML-tabel om, met rowspan/colspan als lege vervolgcellen."""
    rows = rows_of(tbl)
    if not rows:
        return
    grid = []           # lijst van rijen; elke rij is een lijst strings/None
    pending = {}        # kolomindex -> resterend aantal rijen rowspan

    for r in rows:
        line = []
        col = 0
        cs = cells_of(r)
        ci = 0
        while ci < len(cs) or any(v > 0 for v in pending.values()):
            if pending.get(col, 0) > 0:
                pending[col] -= 1
                line.append("")
                col += 1
                continue
            if ci >= len(cs):
                break
            cell = cs[ci]
            ci += 1
            txt = clean(inline_of(cell)).replace("|", "\\|")
            try:
                rs = int(cell.attrs.get("rowspan", 1))
            except ValueError:
                rs = 1
            try:
                span = int(cell.attrs.get("colspan", 1))
            except ValueError:
                span = 1
            line.append(txt)
            if rs > 1:
                pending[col] = rs - 1
            col += 1
            for _ in range(span - 1):
                line.append("")
                col += 1
        grid.append(line)

    width = max(len(r) for r in grid)
    for r in grid:
        r += [""] * (width - len(r))

    out.append("| " + " | ".join(grid[0]) + " |")
    out.append("|" + "---|" * width)
    for r in grid[1:]:
        out.append("| " + " | ".join(r) + " |")
    out.append("")


def walk(node, out, meta):
    for k in node.kids:
        t, c = k.tag, k.cls()

        if t == "h1":
            meta["titel"] = clean(inline_of(k))
            continue
        if t == "p" and "sub" in c:
            meta["sub"] = clean(inline_of(k))
            continue
        if t == "p" and "foot" in c:
            continue
        if t in ("style", "title", "head", "script"):
            continue
        if t == "hr":
            continue

        if "pb" in c.split():
            out.append("<!--pb-->")
            out.append("")

        if t == "h2":
            out.append("## " + clean(inline_of(k)))
            out.append("")
        elif t == "h3":
            out.append("### " + clean(inline_of(k)))
            out.append("")
        elif t == "p":
            txt = clean(inline_of(k))
            if txt:
                out.append(txt)
                out.append("")
        elif t == "ul":
            for li in [x for x in k.kids if x.tag == "li"]:
                out.append("- " + clean(inline_of(li)))
            out.append("")
        elif t == "ol":
            for i, li in enumerate([x for x in k.kids if x.tag == "li"], 1):
                out.append(f"{i}. " + clean(inline_of(li)))
            out.append("")
        elif t == "div" and "kern" in c:
            out.append("!!! kern")
            out.append(clean(inline_of(k)))
            out.append("")
        elif t == "div" and "box" in c:
            out.append("!!! box")
            out.append(clean(inline_of(k)))
            out.append("")
        elif t == "div" and "cta" in c:
            out.append("> " + clean(inline_of(k)))
            out.append("")
        elif t == "table" and "two" in c:
            rows = rows_of(k)
            if not rows:
                continue
            out.append("::: cols")
            for i, cell in enumerate(cells_of(rows[0])):
                if i:
                    out.append("+++")
                sub = []
                walk(cell, sub, meta)
                out.extend(x for x in sub if x != "")
                out.append("")
            out.append(":::")
            out.append("")
        elif t == "table":
            table_md(k, out)
        elif t in ("div", "body", "html", "section"):
            walk(k, out, meta)
        elif t == "#text":
            txt = clean(k.text)
            if txt:
                out.append(txt)
                out.append("")


def main():
    if len(sys.argv) < 2:
        sys.exit("gebruik: python html2dcamd.py <bestand.html> [> uit.src.md]")
    src = open(sys.argv[1], encoding="utf-8").read()
    tr = Tree()
    tr.feed(src)
    out, meta = [], {}
    walk(tr.root, out, meta)

    # dubbele lege regels opruimen
    body, prev_blank = [], False
    for line in out:
        blank = (line.strip() == "")
        if blank and prev_blank:
            continue
        body.append(line)
        prev_blank = blank

    head = [f"<!-- titel: {meta.get('titel', '')} -->"]
    if meta.get("sub"):
        head.append(f"<!-- sub: {meta['sub']} -->")
    head.append("")
    sys.stdout.write("\n".join(head + body).rstrip() + "\n")


if __name__ == "__main__":
    main()
