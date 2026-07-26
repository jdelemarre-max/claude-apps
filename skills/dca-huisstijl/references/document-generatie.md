# DCA-document generatie

Hoe je een DOCX of PDF in DCA-huisstijl maakt.

## Tokens (hardcoded in scripts/dca_document.py)

```python
DIEPBLAUW   = "1B2C5A"  # primair, koppen
DONKERBLAUW = "0F1C3F"  # hover/diepe accenten
GOUD        = "C9A227"  # accentlijn, highlights
CREAM       = "FAF7F0"  # achtergrond (PDF)
KOP_FONT    = "Merriweather"
BODY_FONT   = "Inter"
```

Fonts zijn webfonts; als Merriweather/Inter niet op het systeem staan, valt Word terug op een serif (koppen) en sans-serif (body). Voor een PDF waarin de fonts gegarandeerd kloppen, embed je ze of render je via HTML→PDF met de Google Fonts ingeladen.

## DOCX — snelste route

```bash
pip install python-docx --break-system-packages
python scripts/dca_document.py \
  --type docx \
  --titel "Toptraining 2026" \
  --in body.md \
  --out /mnt/user-data/outputs/toptraining.docx
```

`body.md` is gewone markdown (koppen met #, lijsten, tabellen). Het script:
- zet H1/H2 in Merriweather + diepblauw
- body in Inter
- voegt een gouden accentlijn onder de titel toe
- zet nette marges (2,5 cm)

## PDF in huisstijl

De PDF-tak zit nu in het script. Eén commando:

```bash
python scripts/dca_document.py \
  --type pdf \
  --titel "Russisch — de accusatief" \
  --sub "examenblad · alles wat je morgen nodig hebt" \
  --in body.md \
  --out /mnt/user-data/outputs/accusatief.pdf
```

Rendert via wkhtmltopdf met cream achtergrond, diepblauwe koppen, gouden
accentlijnen en nette A4-marges.

### Bron wordt automatisch bewaard

Het script schrijft `<out>.src.md` naast de PDF, mét titel/sub/lang in
HTML-commentaar. Een volgende versie is daarmee een **edit**, geen herbouw:

```bash
# hoofdstuk toevoegen aan de bron, dan opnieuw renderen
python scripts/dca_document.py --type pdf --titel "" --in accusatief.src.md \
  --out /mnt/user-data/outputs/accusatief.pdf
```

Uitzetten met `--no-source`. **Bewaar de .src.md altijd naast de PDF** — de
werkmap wordt tussen sessies gewist, en zonder bron begint elke wijziging
weer bij nul. Dat was de echte kostenpost, niet de rendering.

### Markdown-subset

| Bron | Resultaat |
|---|---|
| `# / ## / ###` | koppen, H2 met gouden onderlijn |
| `\| a \| b \|` | tabel met diepblauwe header, scheidingsrij optioneel |
| `- ` / `1. ` | bullets / genummerd |
| `!!! kern` | diepblauw kernblok tot de eerste lege regel |
| `!!! box` | wit kader met gouden rand |
| `> tekst` | CTA-blok (gouden linkerrand, cream) |
| `<!--pb-->` | pagina-einde |
| `**vet**` `*cursief*` `` `code` `` `[t](url)` | inline-opmaak |

### RAG-bolletjes

wkhtmltopdf heeft geen kleuren-emoji-font, dus 🔴🟠🟢 komen er anders
**monochroom** uit. Het script vervangt ze door gekleurde spans. Amber wordt
daarbij DCA-goud `#C9A227` in plaats van oranje — de huisstijlregel "nooit
oranje" wint van de standaard-RAG-kleur.

### Fonts

Merriweather/Inter zijn webfonts en staan zelden lokaal. De stack valt terug
op Lora/DejaVu Serif (koppen) en DejaVu Sans (body). Beide dekken Cyrillisch;
dat is bewust — een gewone systeemserif brak eerder op niet-Latijnse tekens.

### Kolommen naast elkaar

```
::: cols
### Linkerkolom
| Nom. mv. | Acc. mv. |
|---|---|
| люди | людей |
+++
### Rechterkolom
| Nom. mv. | Acc. mv. |
|---|---|
| дети | детей |
:::
```

Werkt met twee of meer kolommen; de breedte wordt gelijk verdeeld. Binnen een
kolom mag alles wat de subset kent (koppen, tabellen, bullets).

### Bestaande HTML terugbrengen naar markdown

`scripts/html2dcamd.py` zet een handgebouwd huisstijl-HTML-document om naar de
markdown-subset, zodat ook oudere stukken alsnog een bron krijgen:

```bash
python scripts/html2dcamd.py oud.html > oud.src.md
python scripts/dca_document.py --type pdf --titel "" --in oud.src.md --out nieuw.pdf
```

Herkent `h1`/`p.sub` als front-matter, `div.kern`/`div.box`/`div.cta`,
`table.two` → `::: cols`, `class="pb"` → `<!--pb-->`, `span.end` → `==goud==`.
Rowspan en colspan worden als lege vervolgcellen bewaard, zodat kolommen blijven
uitlijnen.

**Getest op beide accusatiefbladen (NL en EN): nul woordverlies in beide
richtingen.** De regeneratie loopt wel één pagina langer dan het handgebouwde
origineel, doordat inline cel-styling uit het origineel verloren gaat en rijen
iets hoger worden. Controleer de eerste render dus visueel.

## Regels
- Nooit oranje.
- Titel altijd in Merriweather, diepblauw, met gouden lijn eronder.
- DOCX is standaard; PDF alleen op verzoek of bij codewoord DCAnl/DCAen/DCAdui.
