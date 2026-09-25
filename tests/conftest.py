"""Gemeinsame Vorrichtungen für die Tests.

Das Programm ist eine einzelne `.pyw`-Datei und damit über den gewöhnlichen
Import nicht erreichbar; geladen wird es deshalb über einen SourceFileLoader.
Gespeichert wird in den Tests nichts: `load_config` und `save_config` sind
ersetzt, sodass keine Einstellungsdatei entsteht. Die Oberflächentests
bekommen eine erfundene Installation mit erfundenen Paketen - das echte
System wird dabei weder durchsucht noch verändert.
"""

from __future__ import annotations

import copy
import importlib.machinery
import importlib.util
import sys
import time
from pathlib import Path

import pytest

PROGRAMMDATEI = Path(__file__).resolve().parent.parent / "Python-Script & Module Manager.pyw"


@pytest.fixture(scope="session")
def pm():
    """Das Programm als Modul."""
    lader = importlib.machinery.SourceFileLoader("script_module_manager", str(PROGRAMMDATEI))
    spec = importlib.util.spec_from_loader("script_module_manager", lader)
    modul = importlib.util.module_from_spec(spec)
    sys.modules["script_module_manager"] = modul
    lader.exec_module(modul)
    modul.save_config = lambda daten: True
    modul.load_config = lambda: {}
    return modul


def paket(name, version="1.0", top=None, sub=(), requires=()):
    """Paketdaten in der Form, die MODUL_PROBE liefert."""
    return {"name": name, "version": version, "top": list(top or [name.lower()]),
            "sub": list(sub), "requires": list(requires)}


def modul_daten(pakete, toplevel=()):
    """Eingelesene Daten einer erfundenen Installation."""
    return {"stdlib": sorted(set(sys.stdlib_module_names) | {"__future__"}),
            "toplevel": list(toplevel), "pip": True, "zeit": "2026-01-01T10:00:00",
            "dists": pakete}


def tk_wurzel_anlegen(tk, versuche=4):
    """Eine Tk-Wurzel anlegen, notfalls in mehreren Anläufen.

    Auf den Windows-Läufern der CI schlägt das Anlegen gelegentlich mit
    "Can't find a usable init.tcl" fehl, obwohl die Dateien da sind. Das ist
    eine Eigenheit der Umgebung und kein Befund über das Programm - nach ein
    paar Anläufen wird der Test deshalb übersprungen statt als Fehler gemeldet.
    """
    letzter = None
    for nummer in range(versuche):
        try:
            return tk.Tk()
        except tk.TclError as fehler:
            letzter = fehler
            time.sleep(0.5 * (nummer + 1))
    pytest.skip(f"Tk ließ sich nicht starten: {letzter}")
    return None                                  # unerreichbar, der Klarheit halber


@pytest.fixture(scope="session")
def tk_anker():
    """Eine unsichtbare Tk-Wurzel, die den Tcl-Interpreter am Leben hält.

    Zerstört man die letzte Tk-Instanz und legt gleich darauf eine neue an,
    findet Tcl auf manchen Rechnern seine Startdateien nicht mehr. Lässt sich
    schon der Anker nicht anlegen, gibt es keine Anzeige, und alle Tests der
    Oberfläche werden übersprungen.
    """
    tk = pytest.importorskip("tkinter", reason="Tkinter ist nicht verfügbar")
    anker = tk_wurzel_anlegen(tk)
    anker.withdraw()
    yield anker
    anker.destroy()


@pytest.fixture
def grund_cfg(pm, tmp_path):
    """Einstellungen mit einer Installation - dem laufenden Python - und Testdaten."""
    exe = pm.konsolen_python(sys.executable)
    schluessel = pm.normschluessel(exe)
    inst = {"key": schluessel, "exe": exe, "version": "3.12.0", "bits": 64,
            "ordner": "Python312", "marken": ["path"]}
    pakete = [paket("requests", "2.32.0", requires=["idna", "urllib3"]),
              paket("idna", "3.7")]
    return {
        "scripts": [],
        "installationen": [inst],
        "modul_daten": {schluessel: modul_daten(pakete)},
        "bekannte_module": {schluessel: {"requests": "requests", "idna": "idna",
                                         "urllib3": "urllib3"}},
        "modul_aktualisierung": "manuell",
        "ausfuehren_mit": schluessel,
    }


@pytest.fixture
def fenster(pm, tk_anker):
    """Baut Hauptfenster der Anwendung und räumt sie hinterher weg."""
    import tkinter as tk
    from tkinter import ttk

    pm._tk, pm._ttk = tk, ttk
    pm.widgets_bereitstellen()
    offen = []

    class Werkstatt:
        def bauen(self, cfg, sprache="de", schema="light", groesse="1200x800"):
            pm._.language = sprache
            pm.apply_theme(schema)
            pm.load_config = lambda: copy.deepcopy(cfg)
            wurzel = tk_wurzel_anlegen(tk)
            pm.icons_bestimmen(wurzel)
            app = pm.ManagerApp(wurzel)
            wurzel.geometry(f"{groesse}+40+40")
            offen.append(wurzel)
            warten(wurzel, 0.3)
            return app

    yield Werkstatt()

    for wurzel in offen:
        try:
            wurzel.destroy()
        except tk.TclError:                      # war schon zu
            pass
    pm.load_config = lambda: {}
    pm._.language = pm.SOURCE_LANGUAGE
    pm.apply_theme(pm.DEFAULT_THEME)


def warten(wurzel, sekunden, bis=None):
    """Die Ereignisschleife laufen lassen - bis die Zeit um ist oder bis() stimmt."""
    ende = time.monotonic() + sekunden
    while time.monotonic() < ende:
        wurzel.update()
        if bis is not None and bis():
            return True
        time.sleep(0.02)
    return bis() if bis is not None else True


def alle_texte(widget):
    """Beschriftungen aller Widgets unterhalb von widget."""
    import tkinter as tk

    texte = []
    try:
        if "text" in widget.keys():
            texte.append(str(widget.cget("text")))
    except tk.TclError:
        pass
    for kind in widget.winfo_children():
        texte += alle_texte(kind)
    return texte
