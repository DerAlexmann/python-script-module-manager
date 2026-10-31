"""Legt die Lizenzdatei für das Release nach dist und hängt die langen Texte an.

Die Lizenztexte von Python und PyInstaller stehen nicht im Repository, sondern
werden hier aus genau den Fassungen gelesen, mit denen die EXE gebaut wurde. So
passt der ausgelieferte Text zum Inhalt der EXE, auch wenn der Bau später auf
eine neue Fassung wechselt. Fehlt ein Text, bricht der Bau ab: Ein Release mit
lückenhaften Hinweisen soll gar nicht erst entstehen.

Aufruf:     python lizenzen_anfuegen.py
"""

from __future__ import annotations

import sys
from importlib import metadata
from pathlib import Path

HIER = Path(__file__).resolve().parent
QUELLE = HIER / "DRITTANBIETER-LIZENZEN.md"
ZIEL = HIER / "dist" / QUELLE.name

KENNUNG_PYTHON = "PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2"
KENNUNG_PYINSTALLER = "Bootloader Exception"


def python_lizenz() -> Path:
    return Path(sys.base_prefix) / "LICENSE.txt"


def pyinstaller_lizenz() -> Path:
    try:
        dateien = metadata.files("pyinstaller") or []
    except metadata.PackageNotFoundError:
        raise SystemExit("PyInstaller ist nicht installiert.") from None
    treffer = [datei for datei in dateien if datei.name == "COPYING.txt"]
    if len(treffer) != 1:
        raise SystemExit(f"PyInstaller bringt {len(treffer)}-mal COPYING.txt mit, "
                         "erwartet war genau eine Datei.")
    return Path(treffer[0].locate())


def lizenztext(pfad: Path, kennung: str) -> str:
    """Den Text lesen und prüfen, ob es wirklich der erwartete ist."""
    if not pfad.is_file():
        raise SystemExit(f"Lizenztext fehlt: {pfad}")
    text = pfad.read_text(encoding="utf-8")
    if kennung not in text:
        raise SystemExit(f"In {pfad} fehlt die Kennung {kennung!r}.")
    return text.strip()


def zusammenstellen(grundtext: str, python_text: str, pyinstaller_text: str) -> str:
    teile = [grundtext.rstrip(), "---", "# Vollständige Lizenztexte / Full license texts"]
    for titel, text in (("Python", python_text), ("PyInstaller", pyinstaller_text)):
        teile.append(f"## {titel}\n\n````text\n{text}\n````")
    return "\n\n".join(teile) + "\n"


def main() -> None:
    text = zusammenstellen(QUELLE.read_text(encoding="utf-8"),
                           lizenztext(python_lizenz(), KENNUNG_PYTHON),
                           lizenztext(pyinstaller_lizenz(), KENNUNG_PYINSTALLER))
    ZIEL.parent.mkdir(exist_ok=True)
    ZIEL.write_text(text, encoding="utf-8", newline="\n")
    print(f"geschrieben: {ZIEL}  ({len(text)} Zeichen)")


if __name__ == "__main__":
    main()
