"""
sync_alt_data.py — haalt het JSON-codeblok uit de Notion-pagina
"ALT Dashboard Data (auto-sync bron)" en schrijft het naar trading-monitor/data.json.

Waarom: de monitor stond volledig hardcoded in index.html, waardoor hij bleef hangen
op de cijfers van 11 mei 2026. Notion is de bron; dit script is de brug.

Gebruik:  python tools/alt-sync/sync_alt_data.py [doelbestand]
Env:      NOTION_API_KEY        (verplicht)
          NOTION_ALT_DATA_PAGE  (optioneel, default = de bekende pagina-ID)
Exit:     0 = geschreven of ongewijzigd, 1 = fout (dan blijft data.json ongemoeid)
"""
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_PAGE = "3b4cb9b9-b2b4-81cb-a29f-cc5be2bcdeb8"
DEFAULT_DEST = Path("trading-monitor/data.json")
API = "https://api.notion.com/v1"
VERSION = "2022-06-28"

# Sleutels die de monitor nodig heeft; ontbreekt er een, dan is de bron stuk.
REQUIRED = ("today", "currentPrice", "basis", "shares", "cats", "pos", "scn", "so", "snaps")


def api_get(path: str, token: str) -> dict:
    req = urllib.request.Request(
        f"{API}/{path}",
        headers={"Authorization": f"Bearer {token}", "Notion-Version": VERSION},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def find_json_block(page_id: str, token: str) -> str:
    """Eerste code-block met taal json, inclusief kindblokken van toggles e.d."""
    cursor, queue = None, [page_id]
    while queue:
        block_id = queue.pop(0)
        cursor = None
        while True:
            path = f"blocks/{block_id}/children?page_size=100"
            if cursor:
                path += f"&start_cursor={cursor}"
            data = api_get(path, token)
            for b in data.get("results", []):
                if b.get("type") == "code" and b["code"].get("language") == "json":
                    return "".join(t["plain_text"] for t in b["code"]["rich_text"])
                if b.get("has_children"):
                    queue.append(b["id"])
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
    raise LookupError("geen json-codeblok gevonden op de Notion-pagina")


def main() -> int:
    token = os.environ.get("NOTION_API_KEY")
    if not token:
        print("FOUT: NOTION_API_KEY ontbreekt", file=sys.stderr)
        return 1

    page = os.environ.get("NOTION_ALT_DATA_PAGE", DEFAULT_PAGE)
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DEST

    try:
        raw = find_json_block(page, token)
        data = json.loads(raw)
    except (urllib.error.URLError, LookupError, json.JSONDecodeError) as err:
        print(f"FOUT: bron niet bruikbaar ({err}) — {dest} blijft ongewijzigd", file=sys.stderr)
        return 1

    missing = [k for k in REQUIRED if k not in data]
    if missing:
        print(f"FOUT: sleutels ontbreken in de bron: {', '.join(missing)}", file=sys.stderr)
        return 1

    new = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if dest.exists() and dest.read_text(encoding="utf-8") == new:
        print(f"ongewijzigd — {dest}")
        return 0

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(new, encoding="utf-8")
    print(f"bijgewerkt — {dest} (peildatum {data['today']}, koers ${data['currentPrice']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
