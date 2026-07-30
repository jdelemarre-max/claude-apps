#!/usr/bin/env python3
"""Voeg PDF's samen tot één bestand, met bladwijzer per bronbestand.

Gebruik:
    python merge_pdf.py uit.pdf bestand1.pdf bestand2.pdf [...]
"""
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def merge(output: str, inputs: list[str]) -> None:
    ontbreekt = [p for p in inputs if not Path(p).is_file()]
    if ontbreekt:
        raise SystemExit(f"Niet gevonden: {', '.join(ontbreekt)}")

    writer = PdfWriter()
    for pad in inputs:
        reader = PdfReader(pad)
        if reader.is_encrypted:
            reader.decrypt("")  # lege wachtwoord-poging; faalt hard bij echt slot
        start = len(writer.pages)
        for page in reader.pages:
            writer.add_page(page)
        writer.add_outline_item(Path(pad).stem, start)
        print(f"  + {pad}: {len(reader.pages)} pagina's")

    with open(output, "wb") as f:
        writer.write(f)
    print(f"=> {output}: {len(writer.pages)} pagina's totaal")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        raise SystemExit(__doc__)
    merge(sys.argv[1], sys.argv[2:])
