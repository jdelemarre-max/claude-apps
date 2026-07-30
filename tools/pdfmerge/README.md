# pdfmerge

Voegt meerdere PDF's samen tot één bestand, met een bladwijzer (outline) per
bronbestand zodat je in de gecombineerde PDF per document kunt springen.

Verplaatst hierheen vanuit `~/Downloads` tijdens PROFYLAXE-bord5 (30 jul 2026).

## Vereiste

```bash
pip install pypdf
```

## Gebruik

```bash
python merge_pdf.py uit.pdf bestand1.pdf bestand2.pdf [...]
```

- Eerste argument = **uitvoerbestand**.
- Daarna één of meer **invoerbestanden**, in de volgorde waarin ze samengevoegd
  worden.
- Minimaal één uitvoer + twee invoerbestanden vereist (anders print het de help).

## Gedrag

- Ontbrekende invoerbestanden → stopt hard met een melding welke ontbreken
  (geen half product).
- Versleutelde PDF's → probeert te openen met een leeg wachtwoord; faalt hard bij
  een echt slot.
- Per bronbestand wordt een bladwijzer toegevoegd met de bestandsnaam (zonder
  extensie).
- Print per bestand het aantal pagina's en aan het eind het totaal.

## Voorbeeld

```bash
python merge_pdf.py rapport-totaal.pdf intro.pdf hoofdstuk1.pdf bijlage.pdf
```
