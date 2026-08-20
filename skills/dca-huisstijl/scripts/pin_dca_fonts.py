"""
pin_dca_fonts.py — DCA-huisstijl statische fonts genereren (Inter + Merriweather).

Waarom: WeasyPrint rendert variabele fonts onbetrouwbaar; de DCA PDF-skill
vereist statische instanties. Dit script downloadt de variabele fonts uit de
officiele google/fonts GitHub-repo en instantieert de benodigde gewichten.

Gebruik:  python pin_dca_fonts.py [doelmap]     (default: ./fonts)
Vereist:  pip install fonttools requests
Output:   Inter-Regular/SemiBold/Bold.ttf + Merriweather-Regular/Bold/Black.ttf
"""
import sys, io, urllib.request
from pathlib import Path
from fontTools import ttLib
from fontTools.varLib.instancer import instantiateVariableFont

# Windows-console valt terug op cp1252; forceer utf-8 zodat de output-tekens werken.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "https://raw.githubusercontent.com/google/fonts/main/ofl"
SOURCES = {
    "Inter": f"{BASE}/inter/Inter%5Bopsz%2Cwght%5D.ttf",
    "Merriweather": f"{BASE}/merriweather/Merriweather%5Bopsz%2Cwdth%2Cwght%5D.ttf",
}
INSTANCES = {
    "Inter": {"Regular": 400, "SemiBold": 600, "Bold": 700},
    "Merriweather": {"Regular": 400, "Bold": 700, "Black": 900},
}

def main(outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)
    for family, url in SOURCES.items():
        print(f"↓ {family} (variabel) ...")
        data = urllib.request.urlopen(url, timeout=60).read()
        for style, wght in INSTANCES[family].items():
            font = ttLib.TTFont(io.BytesIO(data))
            axes = {"wght": wght}
            # pin overige assen op default
            for ax in font["fvar"].axes:
                if ax.axisTag not in axes:
                    axes[ax.axisTag] = ax.defaultValue
            instantiateVariableFont(font, axes, inplace=True)
            # naamtabel netjes: familie + stijl
            name = font["name"]
            name.setName(f"{family} {style}" if style != "Regular" else family, 1, 3, 1, 0x409)
            name.setName(style if style in ("Regular", "Bold") else "Regular", 2, 3, 1, 0x409)
            name.setName(f"{family} {style}", 4, 3, 1, 0x409)
            name.setName(f"{family}-{style}", 6, 3, 1, 0x409)
            dest = outdir / f"{family}-{style}.ttf"
            font.save(dest)
            print(f"  ✓ {dest.name} ({dest.stat().st_size//1024} KB, wght={wght})")
    print(f"\nKlaar → {outdir.resolve()}")

if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("fonts"))
