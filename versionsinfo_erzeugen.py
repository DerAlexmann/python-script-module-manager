"""Erzeugt versionsinfo.txt - die Versionsangaben für die Windows-EXE.

Der Explorer zeigt unter „Eigenschaften" nur, was in der EXE selbst steht, und
PyInstaller legt von sich aus keine Versionsressource an. Ohne diese Datei
bleiben Produktname, Version und Urheber leer; wer die EXE heruntergeladen hat,
kann dann nicht nachsehen, welche Fassung vor ihm liegt.

Die Angaben stammen aus PROGRAMM und VERSION in der Programmdatei, gepflegt
wird die Version also weiter an genau einer Stelle. Gelesen wird der Quelltext
mit einem Suchausdruck und nicht per Import, damit hier kein Tkinter gebraucht
wird. Die erzeugte Datei ist abgeleitet und steht in .gitignore.

Aufruf:     python versionsinfo_erzeugen.py
Danach:     pyinstaller ... --version-file versionsinfo.txt ...
"""

from __future__ import annotations

import re
from pathlib import Path

HIER = Path(__file__).resolve().parent
QUELLE = HIER / "Python-Script & Module Manager.pyw"
ZIEL = HIER / "versionsinfo.txt"

URHEBER = "Alexander Unverhau"
JAHR = "2026"
BESCHREIBUNG = "Python-Scripts starten und Module aller Python-Installationen verwalten"
HINWEIS = "Lizenzen der mitgelieferten Komponenten: DRITTANBIETER-LIZENZEN.md"
DOWNLOADNAME = "Python-Script-Module-Manager.exe"   # wie ASSET in release.yml

# Windows erwartet die Felder als Quelltext; Umlaute wären hier eine Fehlerquelle
# ohne Not, deshalb kommen die Texte ohne sie aus.
SPRACHE = 1031          # Deutsch, die Ausgangssprache des Programms
ZEICHENSATZ = 1200      # Unicode
GRENZE = 65535          # so weit reicht eine Stelle im Versionsfeld


def aus_quelltext(name: str) -> str:
    """Den Wert einer Zeichenketten-Konstante aus der Programmdatei holen.

    Steht der Name nicht genau einmal am Zeilenanfang, ist Abbrechen richtiger
    als Raten: Python benutzt den letzten Treffer, die Suche vielleicht einen
    anderen.
    """
    text = QUELLE.read_text(encoding="utf-8")
    treffer = re.findall(rf'^{name}\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if len(treffer) != 1:
        raise SystemExit(f"{name} steht {len(treffer)}-mal in {QUELLE.name}, "
                         "erwartet war genau eine Zeile.")
    if not treffer[0].isascii():
        raise SystemExit(f"{name} = {treffer[0]!r} enthält Zeichen außerhalb von ASCII.")
    return treffer[0]


def vierstellig(version: str) -> tuple[int, int, int, int]:
    """„2.0.3" wird zu (2, 0, 3, 0) - Windows erwartet immer vier Zahlen."""
    try:
        zahlen = [int(teil) for teil in version.split(".")]
    except ValueError:
        raise SystemExit(f"VERSION {version!r} muss die Form 1.2.3 haben. Vorabfassungen "
                         "wie 1.2.3rc1 kann Windows nicht abbilden.") from None
    if len(zahlen) > 4:
        raise SystemExit(f"VERSION {version!r} hat mehr als vier Stellen.")
    if any(zahl < 0 or zahl > GRENZE for zahl in zahlen):
        raise SystemExit(f"VERSION {version!r}: jede Stelle muss zwischen 0 und "
                         f"{GRENZE} liegen.")
    zahlen += [0] * (4 - len(zahlen))
    return tuple(zahlen)


def inhalt(name: str, version: str) -> str:
    haupt, neben, flick, bau = vierstellig(version)
    tabelle = f"{SPRACHE:04x}{ZEICHENSATZ:04x}".upper()
    return f"""# Von versionsinfo_erzeugen.py erstellt - nicht von Hand aendern.
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({haupt}, {neben}, {flick}, {bau}),
    prodvers=({haupt}, {neben}, {flick}, {bau}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '{tabelle}',
        [StringStruct('CompanyName', '{URHEBER}'),
        StringStruct('FileDescription', '{BESCHREIBUNG}'),
        StringStruct('FileVersion', {version!r}),
        StringStruct('InternalName', {name!r}),
        StringStruct('LegalCopyright',
                     'Copyright (c) {JAHR} {URHEBER} - MIT-Lizenz - '
                     'erstellt mit Unterstuetzung von Claude AI'),
        StringStruct('OriginalFilename', {DOWNLOADNAME!r}),
        StringStruct('ProductName', {name!r}),
        StringStruct('ProductVersion', {version!r}),
        StringStruct('Comments', '{HINWEIS}')])
      ]),
    VarFileInfo([VarStruct('Translation', [{SPRACHE}, {ZEICHENSATZ}])])
  ]
)
"""


def main() -> None:
    name = aus_quelltext("PROGRAMM")
    version = aus_quelltext("VERSION")
    ZIEL.write_text(inhalt(name, version), encoding="utf-8", newline="\n")
    print(f"geschrieben: {ZIEL}  ({name} {version})")


if __name__ == "__main__":
    main()
