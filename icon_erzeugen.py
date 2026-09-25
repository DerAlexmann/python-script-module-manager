"""Erzeugt das Programmsymbol script_module_manager.ico.

Gezeichnet wird eine Eingabeaufforderung (">_") und darunter rechts ein
Paketwuerfel in Weiss auf einer abgerundeten Flaeche im Akzentblau des
Farbschemas - Scripts starten und Module verwalten. Die .ico enthaelt alle
ueblichen Groessen, vom Reiter der Taskleiste bis zur grossen Kachel im
Explorer.

Aufruf:  python icon_erzeugen.py
Benoetigt:  pip install Pillow
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "script_module_manager.ico")
KANTE = 1024                                  # Vorlage, wird heruntergerechnet
GROESSEN = [16, 24, 32, 48, 64, 128, 256]

BLAU = (47, 125, 225, 255)                    # ACCENT des hellen Schemas
WEISS = (255, 255, 255, 255)


def zeichnen() -> Image.Image:
    bild = Image.new("RGBA", (KANTE, KANTE), (0, 0, 0, 0))
    stift = ImageDraw.Draw(bild)
    rand = KANTE // 16
    stift.rounded_rectangle((rand, rand, KANTE - rand, KANTE - rand),
                            radius=KANTE // 5, fill=BLAU)

    dicke = KANTE // 11

    # Eingabeaufforderung ">" und "_" oben links
    x0, y0, hoehe = KANTE * 0.20, KANTE * 0.22, KANTE * 0.30
    spitze = (x0 + hoehe * 0.62, y0 + hoehe / 2)
    stift.line([(x0, y0), spitze, (x0, y0 + hoehe)], fill=WEISS, width=dicke, joint="curve")
    for punkt in ((x0, y0), (x0, y0 + hoehe)):          # runde Enden
        r = dicke / 2
        stift.ellipse((punkt[0] - r, punkt[1] - r, punkt[0] + r, punkt[1] + r), fill=WEISS)
    strich_y = y0 + hoehe - dicke / 2
    stift.rounded_rectangle((KANTE * 0.44, strich_y, KANTE * 0.60, strich_y + dicke),
                            radius=dicke // 2, fill=WEISS)

    # Paketwuerfel unten rechts: Vorderseite, Deckel, rechte Seite
    mitte_x, oben_y, a = KANTE * 0.68, KANTE * 0.58, KANTE * 0.15
    deckel = [(mitte_x, oben_y), (mitte_x + a, oben_y + a * 0.5),
              (mitte_x, oben_y + a), (mitte_x - a, oben_y + a * 0.5)]
    links = [(mitte_x - a, oben_y + a * 0.5), (mitte_x, oben_y + a),
             (mitte_x, oben_y + a * 2.1), (mitte_x - a, oben_y + a * 1.6)]
    rechts = [(mitte_x, oben_y + a), (mitte_x + a, oben_y + a * 0.5),
              (mitte_x + a, oben_y + a * 1.6), (mitte_x, oben_y + a * 2.1)]
    stift.polygon(deckel, fill=WEISS)
    stift.polygon(links, fill=(225, 235, 250, 255))
    stift.polygon(rechts, fill=(190, 212, 243, 255))
    return bild


def main() -> None:
    vorlage = zeichnen()
    vorlage.save(ZIEL, sizes=[(n, n) for n in GROESSEN])
    print("geschrieben:", ZIEL)


if __name__ == "__main__":
    main()
