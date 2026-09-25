"""
Python-Script & Module Manager 2.0.0 - Scripts starten, Module verwalten

Startet Python-Scripts mit sichtbarer Ausgabe, prueft vorab, ob ihre
Abhaengigkeiten vorhanden sind, und verwaltet die Module jeder gefundenen
Python-Installation - mit Installieren, Deinstallieren und einer Liste, die
sich auch an entfernte Module erinnert.

Farbschema, Sprachumschaltung und Aufbau folgen dem uebrigen Hausstil.

Licensed under MIT License
Copyright 2026 Alexander Unverhau
Created with assistance of Claude AI

Benoetigt nur die Standardbibliothek (Tkinter gehoert dazu).
"""

from __future__ import annotations

import ast
import json
import locale
import math
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime

PROGRAMM = "Python-Script & Module Manager"
VERSION = "2.0.0"

# Von gui_starten() belegt, sobald Tkinter geladen ist.
_tk = None
_ttk = None


# --------------------------------------------------------------------------
# Farbschemata
#
# apply_theme() schreibt die Werte der gewaehlten Palette in die
# Modulvariablen - der uebrige Code benutzt einfach BG, CARD, TEXT ... und
# muss vom Umschalten nichts wissen. Ein eigenes Schema entsteht durch eine
# weitere Palette mit denselben Namen.
# --------------------------------------------------------------------------

THEMES = {
    "light": {
        "BG": "#eef1f5",             # Seitenhintergrund
        "CARD": "#ffffff",           # Karten
        "CARD_ALT": "#fbfcfe",       # Text- und Listenflaechen in Karten
        "BORDER": "#d7dce4",
        "TEXT": "#1b2430",
        "MUTED": "#6c7684",          # Nebentext
        "HEADER": "#1d2330",         # Kopfzeile mit Titel und Umschaltern
        "HEADER_TEXT": "#c2cad8",
        "HEADER_TITLE": "#ffffff",
        "HEADER_GROUP": "#69748c",
        "HEADER_HOVER": "#2b3346",
        "ACCENT": "#2f7de1",
        "ACCENT_DARK": "#1f66c4",
        "ON_ACCENT": "#ffffff",      # Schrift auf farbigen Flaechen
        "OK": "#2e9e5b",
        "OK_DARK": "#25864b",
        "WARN": "#e08b1f",
        "WARN_DARK": "#c4770f",
        "DANGER": "#d64545",
        "DANGER_DARK": "#b83a3a",
        "BTN_BG": "#e3e8f0",         # unauffaelliger Schalter
        "BTN_HOVER": "#d2d9e6",
        "BTN_TEXT": "#1b2430",
        "BTN_DISABLED": "#9aa3b0",
        "FIELD_BG": "#ffffff",       # Eingabefelder
        "TROUGH": "#e3e8f0",         # Rille von Schiebereglern
        "TAB_BG": "#e3e8f0",         # nicht gewaehlter Reiter
        "STATUS_BG": "#e4e8ef",
    },
    "dark": {
        "BG": "#12161d",
        "CARD": "#1a1f28",
        "CARD_ALT": "#151a22",
        "BORDER": "#2c3441",
        "TEXT": "#e6eaf0",
        "MUTED": "#98a2b3",
        "HEADER": "#0e1218",
        "HEADER_TEXT": "#b8c2d0",
        "HEADER_TITLE": "#ffffff",
        "HEADER_GROUP": "#6b7688",
        "HEADER_HOVER": "#212a38",
        "ACCENT": "#4a90e8",
        "ACCENT_DARK": "#3a7ad0",
        "ON_ACCENT": "#ffffff",
        "OK": "#3fb972",
        "OK_DARK": "#349b60",
        "WARN": "#e9a23b",
        "WARN_DARK": "#cc8a26",
        "DANGER": "#e05a5a",
        "DANGER_DARK": "#c44a4a",
        "BTN_BG": "#2a323f",
        "BTN_HOVER": "#353f4f",
        "BTN_TEXT": "#e6eaf0",
        "BTN_DISABLED": "#626c7a",
        "FIELD_BG": "#232b36",
        "TROUGH": "#2a323f",
        "TAB_BG": "#232b36",
        "STATUS_BG": "#0e1218",
    },
}

DEFAULT_THEME = "light"
CURRENT_THEME = DEFAULT_THEME


def apply_theme(name):
    """Farbwerte des gewaehlten Schemas in die Modulvariablen schreiben."""
    global CURRENT_THEME
    CURRENT_THEME = name if name in THEMES else DEFAULT_THEME
    globals().update(THEMES[CURRENT_THEME])


apply_theme(DEFAULT_THEME)      # legt BG, CARD, TEXT ... ueberhaupt erst an

FONT = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_TINY = ("Segoe UI", 8)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_H2 = ("Segoe UI", 12, "bold")
FONT_MONO = ("Consolas", 10)
FONT_MONO_SMALL = ("Consolas", 9)

# Symbole der Icon-Schalter: (Glyphe der Windows-Symbolschrift, Ersatzzeichen).
# Welche Schrift vorhanden ist, klaert icons_bestimmen() nach dem Start von Tk.
ICONS = {
    "start": ("\ue768", "▶"),
    "umbenennen": ("\ue70f", "✎"),
    "abhaengig": ("\ue8fd", "☰"),
    "entfernen": ("\ue74d", "✕"),
    "zurueck": ("\ue76b", "◀"),
    "weiter": ("\ue76c", "▶"),
}
ICON_FONT = None


SYMBOLDATEI = "script_module_manager.ico"


def fenstersymbol_setzen(wurzel):
    """Programmsymbol in die Titelleiste aller Fenster - statt der Tk-Feder.

    Die EXE traegt das Symbol in sich, Windows liest es direkt aus ihr. Das
    Script nimmt die .ico daneben, falls vorhanden; sonst bleibt es bei der
    Voreinstellung von Tk.
    """
    quelle = sys.executable if ist_eingefroren() else os.path.join(programm_ordner(),
                                                                   SYMBOLDATEI)
    if sys.platform == "win32" and os.path.isfile(quelle):
        try:
            wurzel.iconbitmap(default=quelle)
        except _tk.TclError:
            pass


def icons_bestimmen(wurzel):
    """Symbolschrift waehlen: Windows 11, Windows 10 oder gar keine."""
    global ICON_FONT
    from tkinter import font as tkfont
    vorhanden = set(tkfont.families(wurzel))
    for name in ("Segoe Fluent Icons", "Segoe MDL2 Assets"):
        if name in vorhanden:
            ICON_FONT = name
            return


# --------------------------------------------------------------------------
# Sprachumschaltung
#
# Deutsch ist die Quellsprache: im Code steht der deutsche Text, _("...")
# sucht ihn zur Laufzeit in der Sprachtabelle TRANSLATIONS (ganz unten in
# dieser Datei). Dort ist auch beschrieben, wie eine weitere Sprache
# dazukommt.
# --------------------------------------------------------------------------

SOURCE_LANGUAGE = "de"
CONFIG_NAME = "python-script-module-manager.json"
ALTE_CONFIG = "buttons_config.json"         # Script-Liste der Vorgaengerfassung


class Uebersetzt(str):
    """Uebersetzter Text, der seinen deutschen Schluessel kennt.

    Verhaelt sich ueberall wie ein gewoehnlicher String. tr() und
    beschriften() lesen daraus ab, wie sich der Text nach einem Sprachwechsel
    neu bilden laesst - samt der Werte, die mit format() eingesetzt wurden.
    """

    def __new__(cls, text, schluessel, werte=None):
        neu = super().__new__(cls, text)
        neu.schluessel = schluessel
        neu.werte = werte or {}
        return neu

    def format(self, *args, **kwargs):
        if args:                             # Positionsargumente nutzt hier niemand
            return str.format(self, *args, **kwargs)
        return Uebersetzt(str.format(self, **kwargs), self.schluessel, kwargs)


class Translator:
    """Uebersetzt einen deutschen Quelltext in die eingestellte Sprache."""

    def __init__(self, language=SOURCE_LANGUAGE):
        self.language = language

    def __call__(self, text):
        if self.language == SOURCE_LANGUAGE:
            return Uebersetzt(text, text)
        return Uebersetzt(TRANSLATIONS.get(self.language, {}).get(text, text), text)

    def available(self):
        """Sprachkuerzel -> Anzeigename, Quellsprache immer zuerst."""
        names = {SOURCE_LANGUAGE: LANGUAGE_NAMES[SOURCE_LANGUAGE]}
        for code in TRANSLATIONS:
            names[code] = LANGUAGE_NAMES.get(code, code)
        return names


_ = Translator()


def tr(text):
    """Text in die aktuelle Sprache bringen - auch nach einem Sprachwechsel."""
    if isinstance(text, Uebersetzt):
        neu = _(text.schluessel)
        if text.werte:
            return neu.format(**{k: tr(v) for k, v in text.werte.items()})
        return neu
    return text


# --------------------------------------------------------------------------
# Einstellungen
# --------------------------------------------------------------------------

def ist_eingefroren() -> bool:
    """Laeuft das Programm als gebuendelte EXE (PyInstaller & Co.)?"""
    return getattr(sys, "frozen", False)


def programm_ordner() -> str:
    """Ordner, in dem das Programm fuer den Anwender sichtbar liegt.

    Als PyInstaller-EXE mit --onefile entpackt sich das Programm in einen
    temporaeren Ordner (sys._MEIPASS), den PyInstaller beim Beenden wieder
    loescht - __file__ zeigt dorthin. Alles, was den Programmlauf ueberdauern
    soll, gehoert deshalb neben die EXE und nicht neben __file__.
    """
    if ist_eingefroren():
        return os.path.dirname(os.path.abspath(sys.executable))
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:                       # z. B. interaktive Eingabe
        return os.path.expanduser("~")


def config_path():
    """Ablageort der Einstellungen - neben dem Programm."""
    return os.path.join(programm_ordner(), CONFIG_NAME)


def load_config():
    try:
        with open(config_path(), encoding="utf-8") as datei:
            daten = json.load(datei)
        return daten if isinstance(daten, dict) else {}
    except (OSError, ValueError):
        return {}


def save_config(daten):
    """Einstellungen schreiben - erst in eine Zwischendatei, dann austauschen.

    Die Datei enthaelt auch die eingelesenen Modullisten und ist entsprechend
    gross. Ein Absturz mitten im Schreiben soll nicht die Script-Liste kosten.
    """
    ziel = config_path()
    zwischen = ziel + ".tmp"
    try:
        with open(zwischen, "w", encoding="utf-8") as datei:
            json.dump(daten, datei, indent=1, ensure_ascii=False)
        os.replace(zwischen, ziel)
        return True
    except OSError:
        return False


def detect_language():
    """Sprache des Betriebssystems, falls dafuer eine Tabelle vorliegt."""
    try:
        locale.setlocale(locale.LC_CTYPE, "")
        code = (locale.getlocale()[0] or "").lower()
    except (locale.Error, ValueError):
        code = ""
    bekannt = {SOURCE_LANGUAGE, *TRANSLATIONS}
    kurz = code.split("_")[0]
    if kurz in bekannt:
        return kurz
    for name, sprache in (("german", "de"), ("deutsch", "de"), ("english", "en")):
        if kurz.startswith(name) and sprache in bekannt:
            return sprache
    return SOURCE_LANGUAGE


def startup_language(einstellungen):
    """Gespeicherte Sprache, sonst die des Betriebssystems."""
    gespeichert = einstellungen.get("language")
    if gespeichert and (gespeichert == SOURCE_LANGUAGE or gespeichert in TRANSLATIONS):
        return gespeichert
    return detect_language()


# --------------------------------------------------------------------------
# Unterprozesse
# --------------------------------------------------------------------------

# Ohne dieses Flag blitzt bei jedem Aufruf von python.exe ein Konsolenfenster
# auf, sobald der Manager selbst ohne Konsole (pythonw.exe) laeuft.
OHNE_FENSTER = getattr(subprocess, "CREATE_NO_WINDOW", 0)
NEUE_KONSOLE = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)


def utf8_umgebung():
    """Umgebung fuer Unterprozesse: Ausgabe als UTF-8, sofort und ungepuffert."""
    umgebung = os.environ.copy()
    umgebung["PYTHONIOENCODING"] = "utf-8"
    umgebung["PYTHONUNBUFFERED"] = "1"
    return umgebung


def verdeckt_ausfuehren(befehl, timeout=60, cwd=None):
    """Befehl ohne Konsolenfenster ausfuehren; liefert (Exit-Code, stdout, stderr)."""
    ergebnis = subprocess.run(
        befehl, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout, cwd=cwd or tempfile.gettempdir(), env=utf8_umgebung(),
        stdin=subprocess.DEVNULL, creationflags=OHNE_FENSTER)
    return ergebnis.returncode, ergebnis.stdout, ergebnis.stderr


def kanon(name: str) -> str:
    """Paketname in der Schreibweise, unter der pip ihn vergleicht (PEP 503)."""
    return re.sub(r"[-_.]+", "-", name).lower()


# --------------------------------------------------------------------------
# Python-Installationen finden
# --------------------------------------------------------------------------

def konsolen_python(exe: str) -> str:
    """pythonw.exe durch das python.exe daneben ersetzen.

    Scripts und pip laufen immer ueber python.exe: pythonw.exe hat keine
    Standardausgabe, die sich mitlesen liesse.
    """
    if os.path.basename(exe).lower() == "pythonw.exe":
        daneben = os.path.join(os.path.dirname(exe), "python.exe")
        if os.path.isfile(daneben):
            return daneben
    return exe


def normschluessel(exe: str) -> str:
    """Vergleichsschluessel eines Interpreters - Gross/klein und Links egal."""
    return os.path.normcase(os.path.realpath(exe))


def ist_store_platzhalter(pfad: str) -> bool:
    """Liegt der Pfad in WindowsApps? Dort sitzen nur Weiterleitungen.

    Ist Python nicht aus dem Store installiert, oeffnet ein Aufruf dieser
    Platzhalter den Microsoft Store - das soll beim Suchen nicht passieren.
    """
    # Bewusst ohne os.path.normcase: das laesst unter Linux Gross/klein stehen.
    return "\\windowsapps\\" in pfad.replace("/", "\\").lower() + "\\"


SCHNELLABFRAGE = ("import sys;print(sys.executable);"
                  "print('%d.%d.%d' % tuple(sys.version_info[:3]));"
                  "print(64 if sys.maxsize > 2 ** 32 else 32)")


def interpreter_abfragen(exe: str):
    """Tatsaechlichen Pfad, Version und Bitbreite eines Interpreters erfragen.

    Weiterleitungen wie der bin-Ordner des Python-Installationsmanagers
    melden dabei den Interpreter, auf den sie zeigen - so faellt dieselbe
    Installation unter zwei Pfaden nur einmal in die Liste.
    """
    try:
        code, aus, _fehler = verdeckt_ausfuehren([exe, "-c", SCHNELLABFRAGE], timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    zeilen = [z.strip() for z in aus.splitlines() if z.strip()]
    if code != 0 or len(zeilen) < 3:
        return None
    echt = konsolen_python(zeilen[0])
    if not os.path.isfile(echt):
        return None
    return echt, zeilen[1], int(zeilen[2]) if zeilen[2].isdigit() else 0


def _registry_kandidaten():
    """Installationen, die sich nach PEP 514 in der Registry eingetragen haben."""
    if sys.platform != "win32":
        return []
    import winreg
    gefunden = []
    bereiche = (
        (winreg.HKEY_CURRENT_USER, 0),
        (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_64KEY),
        (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_32KEY),
    )
    for wurzel, sicht in bereiche:
        try:
            python = winreg.OpenKey(wurzel, r"Software\Python", 0, winreg.KEY_READ | sicht)
        except OSError:
            continue
        with python:
            for i in range(256):
                try:
                    firma = winreg.EnumKey(python, i)
                except OSError:
                    break
                if firma == "PyLauncher":
                    continue
                try:
                    firmen_schluessel = winreg.OpenKey(python, firma)
                except OSError:
                    continue
                with firmen_schluessel:
                    for j in range(256):
                        try:
                            kennung = winreg.EnumKey(firmen_schluessel, j)
                        except OSError:
                            break
                        try:
                            with winreg.OpenKey(firmen_schluessel,
                                                kennung + r"\InstallPath") as pfad:
                                try:
                                    gefunden.append(winreg.QueryValueEx(pfad, "ExecutablePath")[0])
                                    continue
                                except OSError:
                                    ordner = winreg.QueryValueEx(pfad, "")[0]
                                    gefunden.append(os.path.join(ordner, "python.exe"))
                        except OSError:
                            continue
    return gefunden


def _launcher_kandidaten():
    """Was der Python-Launcher py.exe mit -0p auflistet."""
    gefunden = []
    windows = os.environ.get("WINDIR", r"C:\Windows")
    for launcher in (os.path.join(windows, "py.exe"), shutil.which("py")):
        if not launcher or not os.path.isfile(launcher) or ist_store_platzhalter(launcher):
            continue
        try:
            _code, aus, _fehler = verdeckt_ausfuehren([launcher, "-0p"], timeout=20)
        except (OSError, subprocess.SubprocessError):
            continue
        for zeile in aus.splitlines():
            treffer = re.search(r"([A-Za-z]:\\.*?pythonw?\.exe)\s*$", zeile.strip(), re.I)
            if treffer:
                gefunden.append(treffer.group(1))
    return gefunden


def _ordner_kandidaten():
    """Uebliche Installationsorte, falls die Registry nichts weiss."""
    import glob
    lokal = os.environ.get("LOCALAPPDATA", "")
    muster = [
        os.path.join(lokal, "Programs", "Python", "Python*", "python.exe"),
        os.path.join(lokal, "Python", "pythoncore-*", "python.exe"),
        os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Python*", "python.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
                     "Python*", "python.exe"),
        r"C:\Python*\python.exe",
    ]
    gefunden = []
    for eintrag in muster:
        gefunden.extend(glob.glob(eintrag))
    return gefunden


def pfad_python():
    """Interpreter, den ein schlichtes ``python`` in der Kommandozeile startet."""
    for name in ("python", "python3"):
        pfad = shutil.which(name)
        if pfad and not ist_store_platzhalter(pfad):
            return pfad
    return None


def doppelklick_python():
    """Interpreter, den ein Doppelklick auf eine .pyw- bzw. .py-Datei startet.

    Massgeblich ist die Dateizuordnung. Zeigt sie auf den Launcher
    (py.exe/pyw.exe), entscheidet dessen Voreinstellung - die erfragt man
    am zuverlaessigsten beim Launcher selbst.
    """
    if sys.platform != "win32":
        return None
    import winreg
    for endung in (".pyw", ".py"):
        progid = None
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Explorer"
                                r"\FileExts" + "\\" + endung + r"\UserChoice") as wahl:
                progid = winreg.QueryValueEx(wahl, "ProgId")[0]
        except OSError:
            pass
        try:
            if not progid:
                progid = winreg.QueryValue(winreg.HKEY_CLASSES_ROOT, endung)
            befehl = winreg.QueryValue(winreg.HKEY_CLASSES_ROOT, progid + r"\shell\open\command")
        except OSError:
            continue
        treffer = re.match(r'\s*"([^"]+)"|\s*(\S+)', befehl or "")
        if not treffer:
            continue
        exe = os.path.expandvars(treffer.group(1) or treffer.group(2))
        name = os.path.basename(exe).lower()
        if name in ("py.exe", "pyw.exe"):
            launcher = os.path.join(os.path.dirname(exe), "py.exe")
            if os.path.isfile(launcher) and not ist_store_platzhalter(launcher):
                return launcher
        elif name in ("python.exe", "pythonw.exe"):
            return konsolen_python(exe)
    return None


def installation_titel(inst) -> str:
    """Kurzname einer Installation, z. B. "Python 3.14.7 · Python314"."""
    return f"Python {inst['version']} · {inst['ordner']}"


MARKEN = {
    "path": "Kommandozeile (PATH)",
    "doppelklick": "Doppelklick",
    "selbst": "dieses Programm",
}


def installationen_finden(zusaetzliche=()):
    """Alle erreichbaren Python-Installationen - jede genau einmal.

    Liefert eine Liste von Eintraegen mit Pfad, Version, Bitbreite,
    Ordnername und Marken: welche Installation ``python`` auf der
    Kommandozeile ist, welche ein Doppelklick startet und welche dieses
    Programm gerade ausfuehrt.
    """
    kandidaten = []
    if not ist_eingefroren():
        kandidaten.append(konsolen_python(sys.executable))
    kandidaten += _registry_kandidaten() + _launcher_kandidaten() + _ordner_kandidaten()
    kandidaten += list(zusaetzliche)
    pfad = pfad_python()
    if pfad:
        kandidaten.append(pfad)

    gesehen = set()
    installationen = {}
    for kandidat in kandidaten:
        kandidat = konsolen_python(os.path.abspath(kandidat))
        if not os.path.isfile(kandidat) or ist_store_platzhalter(kandidat):
            continue
        schluessel = normschluessel(kandidat)
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        antwort = interpreter_abfragen(kandidat)
        if not antwort:
            continue
        exe, version, bits = antwort
        echt = normschluessel(exe)
        gesehen.add(echt)
        if echt in installationen:
            continue
        ordner = os.path.dirname(exe)
        if os.path.basename(ordner).lower() in ("scripts", "bin"):     # virtuelle Umgebung
            ordner = os.path.dirname(ordner)
        installationen[echt] = {"key": echt, "exe": exe, "version": version, "bits": bits,
                                "ordner": os.path.basename(ordner) or ordner, "marken": []}

    def markieren(exe, marke):
        if not exe:
            return
        antwort = interpreter_abfragen(exe)
        if antwort and normschluessel(antwort[0]) in installationen:
            installationen[normschluessel(antwort[0])]["marken"].append(marke)

    markieren(pfad, "path")
    markieren(doppelklick_python(), "doppelklick")
    if not ist_eingefroren():
        eigen = normschluessel(konsolen_python(sys.executable))
        if eigen in installationen:
            installationen[eigen]["marken"].append("selbst")

    def sortierung(inst):
        teile = tuple(int(t) if t.isdigit() else 0 for t in inst["version"].split("."))
        return tuple(-t for t in teile), inst["ordner"].lower()
    return sorted(installationen.values(), key=sortierung)


# --------------------------------------------------------------------------
# Module einer Installation einlesen
#
# Das Einlesen laeuft IN der jeweiligen Installation: MODUL_PROBE wird dort
# mit -c ausgefuehrt und meldet als JSON, was sie an Standardbibliothek,
# importierbaren Modulen und installierten Paketen kennt. Nichts davon wird
# importiert - die Angaben stammen aus den Paketdaten (RECORD, METADATA)
# und aus dem Verzeichnis von sys.path.
#
# Fuer verschachtelte Module wird mehr gebraucht als der oberste Name:
# "google" etwa ist ein Namensraum, den google-cloud-storage, protobuf und
# weitere Pakete gemeinsam fuellen. Fuer solche Namen - geteilt oder ohne
# __init__.py - merkt sich die Probe auch die Unterpfade bis zur dritten
# Ebene, damit "google.cloud.storage" dem richtigen Paket zugeordnet wird.
# Der Code muss auch unter aelteren Python-Fassungen laufen (ab 3.8).
# --------------------------------------------------------------------------

MODUL_PROBE = r'''
import json, os, re, sys
sys.path[:] = [p for p in sys.path if p not in ("", ".", os.getcwd())]
e = {"exe": sys.executable, "version": "%d.%d.%d" % tuple(sys.version_info[:3]),
     "bits": 64 if sys.maxsize > 2 ** 32 else 32}
std = set(sys.builtin_module_names)
std.update(getattr(sys, "stdlib_module_names", ()))
if not getattr(sys, "stdlib_module_names", None):
    import sysconfig
    for sl in ("stdlib", "platstdlib"):
        o = sysconfig.get_paths().get(sl)
        if o and os.path.isdir(o):
            for n in os.listdir(o):
                if n in ("site-packages", "dist-packages", "__pycache__"):
                    continue
                if n.endswith(".py"):
                    std.add(n[:-3])
                elif os.path.isdir(os.path.join(o, n)) and re.match(r"^[A-Za-z_]\w*$", n):
                    std.add(n)
    d = os.path.join(getattr(sys, "base_prefix", sys.prefix), "DLLs")
    if os.path.isdir(d):
        for n in os.listdir(d):
            if n.endswith(".pyd"):
                std.add(n.split(".")[0])
std.add("__future__")
e["stdlib"] = sorted(std)
tops = set()
try:
    import pkgutil
    for m in pkgutil.iter_modules():
        tops.add(m.name)
except Exception:
    pass
e["toplevel"] = sorted(tops)
try:
    import importlib.util
    e["pip"] = importlib.util.find_spec("pip") is not None
except Exception:
    e["pip"] = False
Marker = None
for q in ("packaging.markers", "pip._vendor.packaging.markers"):
    try:
        Marker = __import__(q, fromlist=["Marker"]).Marker
        break
    except Exception:
        pass
def gilt(m):
    if not m:
        return True
    if Marker is not None:
        try:
            return bool(Marker(m).evaluate({"extra": ""}))
        except Exception:
            pass
    return "extra" not in m
pakete = []
anzahl = {}
namensraum = set()
try:
    from importlib import metadata
except ImportError:
    metadata = None
gesehen = set()
for d in (metadata.distributions() if metadata else ()):
    try:
        name = d.metadata["Name"]
    except Exception:
        name = None
    if not name:
        continue
    k = re.sub(r"[-_.]+", "-", name).lower()
    if k in gesehen:
        continue
    gesehen.add(k)
    oben, unter, mit_init, tief = set(), set(), set(), set()
    try:
        tl = d.read_text("top_level.txt")
    except Exception:
        tl = None
    if tl:
        oben.update(z.strip() for z in tl.split() if z.strip() and "/" not in z)
    try:
        dateien = d.files or []
    except Exception:
        dateien = []
    for f in dateien:
        teile = list(getattr(f, "parts", ()) or str(f).replace("\\", "/").split("/"))
        if not teile or teile[0] in ("..", "__pycache__") or "__pycache__" in teile:
            continue
        if teile[0].endswith((".dist-info", ".egg-info", ".data")):
            continue
        letzt = teile[-1]
        if "." not in letzt or letzt.rsplit(".", 1)[1].lower() not in ("py", "pyd", "so", "pyc"):
            continue
        stamm = letzt.split(".")[0]
        pfad = teile[:-1] if stamm == "__init__" else teile[:-1] + [stamm]
        if not pfad or not all(re.match(r"^[A-Za-z_]\w*$", t) for t in pfad):
            continue
        oben.add(pfad[0])
        if stamm == "__init__" and len(teile) == 2:
            mit_init.add(pfad[0])
        if len(pfad) > 1:
            tief.add(pfad[0])
        for n in (2, 3):
            if len(pfad) >= n:
                unter.add(".".join(pfad[:n]))
    namensraum.update(tief - mit_init)
    anf = []
    try:
        reqs = d.requires or []
    except Exception:
        reqs = []
    for r in reqs:
        teil, _t, m = r.partition(";")
        t = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", teil)
        if t and gilt(m.strip()):
            anf.append(t.group(1))
    try:
        version = d.version or ""
    except Exception:
        version = ""
    pakete.append({"name": name, "version": version, "top": sorted(oben),
                   "sub": sorted(unter), "requires": sorted(set(anf), key=str.lower)})
    for t in oben:
        anzahl[t] = anzahl.get(t, 0) + 1
for p in pakete:
    p["sub"] = [s for s in p["sub"]
                if anzahl.get(s.split(".")[0], 0) > 1 or s.split(".")[0] in namensraum]
e["dists"] = pakete
sys.stdout.write(json.dumps(e))
'''


def module_einlesen(exe: str) -> dict:
    """MODUL_PROBE in der Installation ausfuehren; liefert ihre Daten.

    Bei einem Fehler enthaelt das Ergebnis nur den Schluessel "fehler".
    """
    try:
        code, aus, fehler = verdeckt_ausfuehren([exe, "-c", MODUL_PROBE], timeout=180)
    except subprocess.TimeoutExpired:
        return {"fehler": "Timeout"}
    except (OSError, subprocess.SubprocessError) as ausnahme:
        return {"fehler": str(ausnahme)}
    if code != 0:
        return {"fehler": (fehler or aus).strip()[-800:] or f"Exit {code}"}
    try:
        daten = json.loads(aus.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {"fehler": aus.strip()[-800:]}
    daten["zeit"] = datetime.now().isoformat(timespec="seconds")
    return daten


class ModulIndex:
    """Nachschlagetabellen zu den eingelesenen Daten einer Installation."""

    def __init__(self, daten: dict):
        self.stdlib = set(daten.get("stdlib", ()))
        self.toplevel = set(daten.get("toplevel", ()))
        self.pip = daten.get("pip", False)
        self.pakete = {}           # kanonischer Name -> Paketdaten
        self.nach_top = {}         # oberster Importname -> [Paketdaten]
        self.nach_unter = {}       # "a.b" / "a.b.c" -> [Paketdaten]
        self.rueck = {}            # kanonischer Name -> [Namen der Pakete, die es brauchen]
        for paket in daten.get("dists", ()):
            self.pakete[kanon(paket["name"])] = paket
            for top in paket.get("top", ()):
                self.nach_top.setdefault(top, []).append(paket)
            for unter in paket.get("sub", ()):
                self.nach_unter.setdefault(unter, []).append(paket)
        self.mit_unterpfaden = {u.split(".")[0] for u in self.nach_unter}
        for paket in daten.get("dists", ()):
            for anforderung in paket.get("requires", ()):
                self.rueck.setdefault(kanon(anforderung), []).append(paket["name"])

    def ist_installiert(self, name: str) -> bool:
        return kanon(name) in self.pakete

    def pakete_fuer(self, modul: str, kandidaten=()):
        """Pakete, die das (auch verschachtelte) Modul bereitstellen.

        None: kein Paket kennt den obersten Namen.
        []:   der oberste Name ist ein Namensraum, aber der verlangte
              Unterpfad gehoert zu keinem installierten Paket.
        """
        top = modul.split(".")[0]
        pakete = self.nach_top.get(top)
        if not pakete:
            return None
        if top not in self.mit_unterpfaden:
            return pakete
        for name in sorted({*kandidaten, modul}, key=lambda n: -n.count(".")):
            teile = name.split(".")
            for tiefe in (3, 2):
                if len(teile) >= tiefe:
                    treffer = self.nach_unter.get(".".join(teile[:tiefe]))
                    if treffer:
                        return treffer
        if "." not in modul and not kandidaten:
            return pakete                    # nur "import google" - der Namensraum genuegt
        return []


# --------------------------------------------------------------------------
# Abhaengigkeiten eines Scripts
# --------------------------------------------------------------------------

# Importname -> pip-Paket, wo beide verschieden heissen.
PAKETNAMEN = {
    "PIL": "pillow", "cv2": "opencv-python", "yaml": "pyyaml", "sklearn": "scikit-learn",
    "skimage": "scikit-image", "bs4": "beautifulsoup4", "Crypto": "pycryptodome",
    "Cryptodome": "pycryptodomex", "dateutil": "python-dateutil", "dotenv": "python-dotenv",
    "serial": "pyserial", "usb": "pyusb", "OpenGL": "PyOpenGL", "docx": "python-docx",
    "pptx": "python-pptx", "fitz": "PyMuPDF", "magic": "python-magic", "jwt": "PyJWT",
    "attr": "attrs", "git": "GitPython", "telegram": "python-telegram-bot",
    "websocket": "websocket-client", "zmq": "pyzmq", "Levenshtein": "python-Levenshtein",
    "webview": "pywebview", "send2trash": "Send2Trash", "googleapiclient":
    "google-api-python-client", "mpl_toolkits": "matplotlib", "pkg_resources": "setuptools",
    "OpenSSL": "pyOpenSSL", "win32api": "pywin32", "win32con": "pywin32",
    "win32gui": "pywin32", "win32com": "pywin32", "win32clipboard": "pywin32",
    "win32process": "pywin32", "win32event": "pywin32", "win32file": "pywin32",
    "win32print": "pywin32", "win32ui": "pywin32", "pythoncom": "pywin32",
    "pywintypes": "pywin32", "winshell": "winshell", "wx": "wxPython",
    "gi": "PyGObject", "Xlib": "python-xlib", "pyi_splash": "pyinstaller",
    "slugify": "python-slugify", "multipart": "python-multipart", "jose": "python-jose",
    "ruamel": "ruamel.yaml", "dns": "dnspython", "nacl": "PyNaCl", "psycopg2": "psycopg2-binary",
    "MySQLdb": "mysqlclient", "sounddevice": "sounddevice", "speech_recognition":
    "SpeechRecognition", "pydub": "pydub", "tkinterdnd2": "tkinterdnd2", "ttkbootstrap":
    "ttkbootstrap", "customtkinter": "customtkinter", "pystray": "pystray",
    "pynput": "pynput", "keyboard": "keyboard", "mouse": "mouse", "pyautogui": "PyAutoGUI",
    "pillow_heif": "pillow-heif", "qrcode": "qrcode", "pypdf": "pypdf", "PyPDF2": "PyPDF2",
    "reportlab": "reportlab", "clr": "pythonnet", "icoextract": "icoextract",
}


class ImportSammler(ast.NodeVisitor):
    """Sammelt die Importe eines Scripts - mit Blick auf verschachtelte Faelle.

    - Relative Importe (``from . import x``) gehoeren zum Script und werden
      uebergangen.
    - Importe in einem try-Block, der ImportError abfaengt, gelten als
      optional: Das Script kommt auch ohne sie aus. Beendet der
      except-Zweig das Script aber (return, raise, sys.exit), ist das Modul
      trotzdem Pflicht - der Block sorgt dann nur fuer eine lesbare Meldung.
    - Was nur unter ``if TYPE_CHECKING:`` steht, wird zur Laufzeit nie
      geladen.
    - ``importlib.import_module("x")`` und ``__import__("x")`` mit festem
      Namen zaehlen ebenfalls.
    - Bei ``from a.b import c`` kann c ein Untermodul sein; "a.b.c" wird als
      Kandidat vermerkt, damit Namensraum-Pakete richtig zugeordnet werden.
    """

    FAENGT = {"ImportError", "ModuleNotFoundError", "Exception", "BaseException"}

    def __init__(self):
        self.funde = {}            # Modul -> {"optional": bool, "zeile": int, "kandidaten": set}
        self._optional = 0

    def _merken(self, modul, zeile, kandidaten=()):
        if not modul or modul.split(".")[0] in ("__future__", "__main__"):
            return
        eintrag = self.funde.setdefault(modul, {"optional": True, "zeile": zeile,
                                                "kandidaten": set()})
        eintrag["optional"] = eintrag["optional"] and self._optional > 0
        eintrag["zeile"] = min(eintrag["zeile"], zeile)
        eintrag["kandidaten"].update(kandidaten)

    def _faengt_importfehler(self, handler) -> bool:
        if handler.type is None:
            return True
        typen = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
        for typ in typen:
            name = typ.attr if isinstance(typ, ast.Attribute) else getattr(typ, "id", "")
            if name in self.FAENGT:
                return True
        return False

    @staticmethod
    def _beendet(handler) -> bool:
        """Verlaesst der except-Zweig das Script oder die Funktion?"""
        for knoten in ast.walk(handler):
            if isinstance(knoten, (ast.Raise, ast.Return)):
                return True
            if isinstance(knoten, ast.Call):
                name = (knoten.func.attr if isinstance(knoten.func, ast.Attribute)
                        else getattr(knoten.func, "id", ""))
                if name in ("exit", "quit", "_exit"):
                    return True
        return False

    def visit_Try(self, node):
        optional = any(self._faengt_importfehler(h) and not self._beendet(h)
                       for h in node.handlers)
        self._optional += optional
        for kind in node.body:
            self.visit(kind)
        self._optional -= optional
        for kind in (*node.handlers, *node.orelse, *node.finalbody):
            self.visit(kind)

    visit_TryStar = visit_Try

    def visit_If(self, node):
        test = node.test
        name = test.attr if isinstance(test, ast.Attribute) else getattr(test, "id", "")
        if name == "TYPE_CHECKING":
            for kind in node.orelse:
                self.visit(kind)
            return
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self._merken(alias.name, node.lineno)

    def visit_ImportFrom(self, node):
        if node.level or not node.module:
            return                           # relativ: gehoert zum Script selbst
        kandidaten = {f"{node.module}.{a.name}" for a in node.names if a.name != "*"}
        self._merken(node.module, node.lineno, kandidaten)

    def visit_Call(self, node):
        funktion = node.func
        name = funktion.attr if isinstance(funktion, ast.Attribute) else getattr(funktion, "id", "")
        if (name in ("import_module", "__import__") and node.args
                and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)
                and not node.args[0].value.startswith(".")):
            self._merken(node.args[0].value, node.lineno)
        self.generic_visit(node)


def importe_lesen(pfad: str):
    """Importe eines Scripts; liefert (Funde, Syntaxfehler oder None)."""
    with open(pfad, "rb") as datei:
        quelltext = datei.read()
    try:
        baum = ast.parse(quelltext, filename=pfad)
    except SyntaxError as fehler:
        return {}, (fehler.lineno or 0, fehler.msg or "")
    except ValueError as fehler:             # z. B. Nullbytes in der Datei
        return {}, (0, str(fehler))
    sammler = ImportSammler()
    sammler.visit(baum)
    return sammler.funde, None


def ist_lokal(modul: str, ordner: str) -> bool:
    """Liegt das Modul neben dem Script? Python sucht dort zuerst."""
    top = modul.split(".")[0]
    for endung in (".py", ".pyw", ".pyd"):
        if os.path.isfile(os.path.join(ordner, top + endung)):
            return True
    unter = os.path.join(ordner, top)
    if os.path.isdir(unter):
        try:
            return any(n.endswith(".py") for n in os.listdir(unter))
        except OSError:
            return False
    return False


NAMENSRAEUME = ("google", "azure", "zope", "jaraco", "sphinxcontrib", "backports")


def paket_vorschlag(modul: str, weitere_indizes=(), kandidaten=()) -> str:
    """Name, unter dem sich ein fehlendes Modul vermutlich installieren laesst."""
    top = modul.split(".")[0]
    if top in NAMENSRAEUME and kandidaten:
        # from google.cloud import storage -> google.cloud.storage
        modul = max(kandidaten, key=lambda n: n.count("."))
    if top in PAKETNAMEN:
        return PAKETNAMEN[top]
    for index in weitere_indizes:            # kennt eine andere Installation das Modul?
        pakete = index.pakete_fuer(modul, kandidaten)
        if pakete:
            return pakete[0]["name"]
    teile = modul.split(".")
    if len(teile) > 1 and top in NAMENSRAEUME:
        return "-".join(teile[:3])
    return top


def abhaengigkeiten_pruefen(pfad: str, funde: dict, index: ModulIndex | None, weitere=()):
    """Importe eines Scripts gegen die Daten einer Installation pruefen."""
    ergebnis = {"stdlib": [], "extern": [], "lokal": [], "fehlt": [], "optional": [],
                "unbekannt": []}
    ordner = os.path.dirname(os.path.abspath(pfad))
    for modul in sorted(funde, key=str.lower):
        fund = funde[modul]
        top = modul.split(".")[0]
        if index is None:
            ergebnis["unbekannt"].append(modul)
            continue
        # Python sucht zuerst neben dem Script - eine gleichnamige Datei dort
        # verdeckt also auch ein installiertes Paket.
        lokal = ist_lokal(modul, ordner)
        if top in index.stdlib and not lokal:
            ergebnis["stdlib"].append(modul)
            continue
        if lokal:
            ergebnis["lokal"].append(modul)
            continue
        pakete = index.pakete_fuer(modul, fund["kandidaten"])
        if pakete:
            ergebnis["extern"].append((modul, [(p["name"], p["version"]) for p in pakete]))
            continue
        if pakete is None and top in index.toplevel:
            ergebnis["extern"].append((modul, []))       # importierbar, aber ohne Paketdaten
            continue
        eintrag = (modul, paket_vorschlag(modul, weitere, fund["kandidaten"]))
        ergebnis["optional" if fund["optional"] else "fehlt"].append(eintrag)
    return ergebnis


# --------------------------------------------------------------------------
# Bausteine der Oberflaeche
#
# faerben() merkt sich zu jedem Widget, welche Rolle seine Farben haben
# ("CARD", "TEXT", ...), beschriften() merkt sich den Uebersetzungsschluessel
# jeder Beschriftung. Sprache und Farbschema lassen sich dadurch umschalten,
# ohne die Oberflaeche neu aufzubauen.
# --------------------------------------------------------------------------

FlatButton = None
IconKnopf = None

# (Widget, Rollen) - Rollen ist None bei Widgets, die sich selbst umfaerben.
GEFAERBTE_WIDGETS: list = []


def faerben(widget, **rollen):
    """Widget einfaerben und die Farbrollen fuer spaeteres Umfaerben merken.

    Beispiel:  faerben(label, bg="CARD", fg="TEXT")
    """
    GEFAERBTE_WIDGETS.append((widget, rollen))
    widget.configure(**{option: THEMES[CURRENT_THEME][name] for option, name in rollen.items()})
    return widget


def farben_auffrischen():
    """Alle gemerkten Widgets auf die aktuelle Palette umstellen.

    Zerstoerte Widgets fallen dabei aus der Liste heraus; Tk meldet sie mit
    einem TclError, was hier das Aufraeumkriterium ist.
    """
    palette = THEMES[CURRENT_THEME]
    uebrig = []
    for widget, rollen in GEFAERBTE_WIDGETS:
        try:
            if rollen is None:
                widget.neu_faerben()
            else:
                widget.configure(**{opt: palette[name] for opt, name in rollen.items()})
        except _tk.TclError:                 # Widget existiert nicht mehr
            continue
        uebrig.append((widget, rollen))
    GEFAERBTE_WIDGETS[:] = uebrig


# (Setzfunktion, Schluessel, Werte) - fuer den Sprachwechsel ohne Neuaufbau
BESCHRIFTUNGEN: list = []


def beschriftung_merken(setzen, text):
    """setzen(text) ausfuehren und - stammt der Text aus _() - fuer spaeter merken."""
    setzen(text)
    if isinstance(text, Uebersetzt):
        BESCHRIFTUNGEN.append((setzen, text.schluessel, text.werte))


def beschriften(widget, text, option="text"):
    """Widget beschriften und den Text fuer den Sprachwechsel merken."""
    beschriftung_merken(lambda neu: widget.configure(**{option: neu}), text)
    return widget


def texte_auffrischen():
    """Alle gemerkten Beschriftungen in die aktuelle Sprache bringen."""
    uebrig = []
    for setzen, schluessel, werte in BESCHRIFTUNGEN:
        text = _(schluessel)
        try:
            setzen(text.format(**{k: tr(v) for k, v in werte.items()}) if werte else text)
        except _tk.TclError:                 # Widget existiert nicht mehr
            continue
        uebrig.append((setzen, schluessel, werte))
    BESCHRIFTUNGEN[:] = uebrig


def zeichnen_anhalten(fenster_id):
    """Haelt das Zeichnen eines Fensters samt Inhalt an; liefert die Fortsetzung.

    Beim Umschalten von Sprache oder Farbschema aendern sich Dutzende
    Elemente. Mit WM_SETREDRAW laesst Windows das alte Bild stehen, bis alles
    fertig ist; danach wird in einem Zug neu gezeichnet. Die Fortsetzung muss
    auch im Fehlerfall laufen - der Aufruf gehoert in ein try/finally.
    """
    if sys.platform != "win32":
        return lambda: None
    try:
        import ctypes
        benutzer = ctypes.windll.user32
        benutzer.SendMessageW(fenster_id, 0x000B, 0, 0)      # WM_SETREDRAW aus
    except (AttributeError, OSError):
        return lambda: None

    def fortsetzen():
        benutzer.SendMessageW(fenster_id, 0x000B, 1, 0)      # WM_SETREDRAW an
        # RDW_INVALIDATE | RDW_ALLCHILDREN | RDW_UPDATENOW
        benutzer.RedrawWindow(fenster_id, None, None, 0x0001 | 0x0080 | 0x0100)
    return fortsetzen


class Tooltip:
    """Hinweisfenster beim Verweilen mit der Maus.

    Der Text darf eine Funktion sein; sie wird erst beim Zeigen aufgerufen.
    So steht im Hinweis immer der aktuelle Stand - und die aktuelle Sprache.
    """

    VERZOEGERUNG_MS = 450

    def __init__(self, widget, text, warnung=None):
        self.widget = widget
        self.text = text
        self.warnung = warnung               # Funktion -> True, wenn der Hinweis warnt
        self.fenster = None
        self.auftrag = None
        widget.bind("<Enter>", self._planen, add="+")
        widget.bind("<Leave>", self._verbergen, add="+")
        widget.bind("<ButtonPress>", self._verbergen, add="+")

    def _planen(self, ereignis):
        self._verbergen()
        self.auftrag = self.widget.after(self.VERZOEGERUNG_MS,
                                         lambda: self._zeigen(ereignis.x_root, ereignis.y_root))

    def _zeigen(self, x, y):
        self.auftrag = None
        try:
            if not self.widget.winfo_ismapped():
                return
        except _tk.TclError:                 # Widget wurde inzwischen zerstoert
            return
        text = self.text() if callable(self.text) else tr(self.text)
        if not text:
            return
        warnt = bool(self.warnung and self.warnung())
        palette = THEMES[CURRENT_THEME]
        fenster = self.fenster = _tk.Toplevel(self.widget)
        fenster.wm_overrideredirect(True)
        fenster.attributes("-topmost", True)
        rahmen = _tk.Frame(fenster, bg=palette["WARN" if warnt else "BORDER"], padx=1, pady=1)
        rahmen.pack()
        _tk.Label(rahmen, text=text, justify="left", font=FONT_SMALL, bg=palette["CARD"],
                  fg=palette["TEXT"], padx=10, pady=6).pack()
        fenster.update_idletasks()
        breite, hoehe = fenster.winfo_reqwidth(), fenster.winfo_reqheight()
        rechts = self.widget.winfo_screenwidth()
        unten = self.widget.winfo_screenheight()
        x = min(x + 14, rechts - breite - 4)
        y = y + 18 if y + 18 + hoehe < unten else y - hoehe - 8
        fenster.wm_geometry(f"+{max(0, x)}+{max(0, y)}")

    def _verbergen(self, _ereignis=None):
        if self.auftrag is not None:
            self.widget.after_cancel(self.auftrag)
            self.auftrag = None
        if self.fenster is not None:
            self.fenster.destroy()
            self.fenster = None


def widgets_bereitstellen():
    """Definiert die Widget-Klassen, sobald Tkinter geladen ist."""
    global FlatButton, IconKnopf

    class _FlatButton(_tk.Button):
        """Flacher Button mit Hover-Effekt in mehreren Farbvarianten."""

        @staticmethod
        def styles():
            """Farbvarianten - erst beim Aufruf gelesen, damit das Schema stimmt."""
            return {
                "primary":   (ACCENT, ACCENT_DARK, ON_ACCENT),
                "secondary": (BTN_BG, BTN_HOVER, BTN_TEXT),
                "success":   (OK, OK_DARK, ON_ACCENT),
                "warn":      (WARN, WARN_DARK, ON_ACCENT),
                "danger":    (DANGER, DANGER_DARK, ON_ACCENT),
            }

        def __init__(self, parent, text, command=None, kind="secondary", tooltip=None, **kw):
            kw.setdefault("padx", 12)
            kw.setdefault("pady", 5)
            super().__init__(parent, text=text, command=command, relief="flat", bd=0,
                             highlightthickness=0, cursor="hand2", font=FONT_SMALL, **kw)
            self._kind = kind
            beschriften(self, text)                  # merkt sich uebersetzte Texte
            self.neu_faerben()
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
            GEFAERBTE_WIDGETS.append((self, None))       # faerbt sich selbst
            if tooltip:
                Tooltip(self, tooltip)

        def art_setzen(self, kind):
            self._kind = kind
            self.neu_faerben()

        def neu_faerben(self):
            """Farben der eigenen Variante aus der aktuellen Palette holen."""
            styles = self.styles()
            bg, hover, fg = styles.get(self._kind, styles["secondary"])
            self._bg, self._hover = bg, hover
            self.configure(bg=bg, fg=fg, activebackground=hover, activeforeground=fg,
                           disabledforeground=BTN_DISABLED)

        def _enabled(self):
            return str(self["state"]) != "disabled"

        def _on_enter(self, _e):
            if self._enabled():
                self.configure(bg=self._hover)

        def _on_leave(self, _e):
            self.configure(bg=self._bg)

    class _IconKnopf(_tk.Button):
        """Kleiner Schalter, der nur ein Symbol zeigt - Erklaerung im Tooltip."""

        def __init__(self, parent, icon, command, tooltip, rolle="MUTED",
                     hover_rolle="ACCENT", grund="CARD_ALT", groesse=11):
            glyphe, ersatz = ICONS[icon]
            schrift = (ICON_FONT, groesse) if ICON_FONT else ("Segoe UI Symbol", groesse)
            super().__init__(parent, text=glyphe if ICON_FONT else ersatz, command=command,
                             relief="flat", bd=0, highlightthickness=0, cursor="hand2",
                             font=schrift, width=2, padx=6, pady=2)
            self._rollen = (rolle, hover_rolle, grund)
            self.neu_faerben()
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
            GEFAERBTE_WIDGETS.append((self, None))
            Tooltip(self, tooltip)

        def neu_faerben(self):
            palette = THEMES[CURRENT_THEME]
            rolle, hover, grund = self._rollen
            self.configure(bg=palette[grund], fg=palette[rolle],
                           activebackground=palette["BTN_HOVER"],
                           activeforeground=palette[hover],
                           disabledforeground=palette["BTN_DISABLED"])

        def _on_enter(self, _e):
            if str(self["state"]) != "disabled":
                palette = THEMES[CURRENT_THEME]
                self.configure(bg=palette["BTN_HOVER"], fg=palette[self._rollen[1]])

        def _on_leave(self, _e):
            self.neu_faerben()

    FlatButton = _FlatButton
    IconKnopf = _IconKnopf


def make_card(parent, **pack_kw):
    """Karte mit dünnem Rahmen."""
    card = faerben(_tk.Frame(parent, highlightthickness=1),
                   bg="CARD", highlightbackground="BORDER", highlightcolor="BORDER")
    if pack_kw:
        card.pack(**pack_kw)
    return card


def card_title(parent, text, **pack_kw):
    etikett = beschriften(faerben(_tk.Label(parent, font=FONT_BOLD, anchor="w"),
                                  bg="CARD", fg="TEXT"), text)
    etikett.pack(**(pack_kw or {"fill": "x", "padx": 14, "pady": (12, 6)}))
    return etikett


def card_text(parent, text, rolle="MUTED", font=None, wraplength=620):
    """Fliesstext in einer Karte."""
    etikett = beschriften(faerben(
        _tk.Label(parent, font=font or FONT_SMALL, justify="left", anchor="w",
                  wraplength=wraplength),
        bg="CARD", fg=rolle), text)
    etikett.pack(fill="x", padx=14, pady=(0, 10))
    return etikett


def textfeld(eltern, hoehe=10, schrift=None):
    """Mehrzeiliges Textfeld mit Rollbalken, schreibgeschuetzt."""
    rahmen = faerben(_tk.Frame(eltern, highlightthickness=1), bg="FIELD_BG",
                     highlightbackground="BORDER", highlightcolor="BORDER")
    feld = faerben(_tk.Text(rahmen, height=hoehe, wrap="word", relief="flat", bd=0,
                            font=schrift or FONT_MONO_SMALL, padx=8, pady=6,
                            state="disabled", cursor="arrow"),
                   bg="FIELD_BG", fg="TEXT", insertbackground="TEXT",
                   selectbackground="ACCENT", selectforeground="ON_ACCENT")
    rollen = _ttk.Scrollbar(rahmen, orient="vertical", command=feld.yview)
    feld.configure(yscrollcommand=rollen.set)
    rollen.pack(side="right", fill="y")
    feld.pack(side="left", fill="both", expand=True)
    return rahmen, feld


def text_tags_faerben(feld):
    """Farbige Markierungen eines Textfelds aus der aktuellen Palette setzen."""
    palette = THEMES[CURRENT_THEME]
    feld.tag_configure("fehler", foreground=palette["DANGER"])
    feld.tag_configure("info", foreground=palette["ACCENT"])
    feld.tag_configure("ok", foreground=palette["OK"])
    feld.tag_configure("warn", foreground=palette["WARN"])
    feld.tag_configure("leise", foreground=palette["MUTED"])
    feld.tag_configure("kopf", foreground=palette["TEXT"], font=("Segoe UI", 10, "bold"))


def text_schreiben(feld, text, tag=None, ans_ende=True):
    feld.configure(state="normal")
    feld.insert("end", text, tag or ())
    feld.configure(state="disabled")
    if ans_ende:
        feld.see("end")


def text_leeren(feld):
    feld.configure(state="normal")
    feld.delete("1.0", "end")
    feld.configure(state="disabled")


def fenster_zentrieren(fenster, ueber, breite=None, hoehe=None):
    """Fenster mittig ueber ein anderes legen, ohne den Bildschirm zu verlassen."""
    fenster.update_idletasks()
    breite = breite or fenster.winfo_reqwidth()
    hoehe = hoehe or fenster.winfo_reqheight()
    x = ueber.winfo_rootx() + (ueber.winfo_width() - breite) // 2
    y = ueber.winfo_rooty() + (ueber.winfo_height() - hoehe) // 3
    x = max(0, min(x, fenster.winfo_screenwidth() - breite))
    y = max(0, min(y, fenster.winfo_screenheight() - hoehe - 40))
    fenster.geometry(f"+{x}+{y}")


class Dialog:
    """Modale Rueckfrage im Farbschema des Programms.

    knoepfe:   [(Beschriftung, Rueckgabewert, Variante)] - der letzte ist die
               Hauptaktion und reagiert auch auf die Eingabetaste.
    optionen:  [(Beschriftung, Wert)] als Auswahlknoepfe, z. B. das Ziel einer
               Installation.
    eingabe:   Vorgabetext eines Eingabefelds (None = kein Feld).
    Nach dem Schliessen stehen Knopf, Option und Eingabe in ergebnis,
    option und eingabe_text; Escape und das Schliesskreuz liefern None.
    """

    def __init__(self, app, titel, text, knoepfe, optionen=None, vorwahl=None,
                 eingabe=None, hinweis=None, hinweis_rolle="WARN", breite=480):
        tk, ttk = _tk, _ttk
        self.ergebnis = None
        self.option = None
        self.eingabe_text = None
        eltern = app.master
        fenster = self.fenster = tk.Toplevel(eltern)
        fenster.withdraw()
        fenster.title(titel)
        fenster.transient(eltern)
        fenster.resizable(False, False)
        faerben(fenster, bg="BG")

        karte = make_card(fenster, fill="both", expand=True, padx=12, pady=12)
        card_title(karte, titel)
        card_text(karte, text, rolle="TEXT", wraplength=round(breite * app.skalierung))
        if hinweis:
            card_text(karte, hinweis, rolle=hinweis_rolle,
                      wraplength=round(breite * app.skalierung))

        self.var_option = tk.StringVar(value=vorwahl or (optionen[0][1] if optionen else ""))
        if optionen:
            gruppe = faerben(tk.Frame(karte), bg="CARD")
            gruppe.pack(fill="x", padx=14, pady=(0, 10))
            for beschriftung, wert in optionen:
                faerben(tk.Radiobutton(gruppe, text=beschriftung, value=wert,
                                       variable=self.var_option, font=FONT_SMALL, anchor="w",
                                       highlightthickness=0, bd=0, cursor="hand2"),
                        bg="CARD", fg="TEXT", activebackground="CARD",
                        activeforeground="TEXT", selectcolor="FIELD_BG").pack(fill="x", pady=1)

        self.var_eingabe = tk.StringVar(value=eingabe or "")
        if eingabe is not None:
            feld = ttk.Entry(karte, textvariable=self.var_eingabe, font=FONT)
            feld.pack(fill="x", padx=14, pady=(0, 12))
            feld.focus_set()
            feld.select_range(0, "end")

        leiste = faerben(tk.Frame(karte), bg="CARD")
        leiste.pack(fill="x", padx=14, pady=(4, 14))
        for beschriftung, wert, art in reversed(knoepfe):
            FlatButton(leiste, beschriftung, lambda w=wert: self._fertig(w),
                       kind=art).pack(side="right", padx=(8, 0))

        haupt = knoepfe[-1][1]
        fenster.bind("<Return>", lambda _e: self._fertig(haupt))
        fenster.bind("<Escape>", lambda _e: self._fertig(None))
        fenster.protocol("WM_DELETE_WINDOW", lambda: self._fertig(None))
        fenster_zentrieren(fenster, eltern)
        fenster.deiconify()
        fenster.grab_set()
        if eingabe is None:
            fenster.focus_set()
        eltern.wait_window(fenster)

    def _fertig(self, wert):
        self.ergebnis = wert
        self.option = self.var_option.get()
        self.eingabe_text = self.var_eingabe.get().strip()
        self.fenster.grab_release()
        self.fenster.destroy()


def melden(app, titel, text, art="info"):
    """Einfache Meldung mit OK-Schalter."""
    Dialog(app, titel, text, [(_("OK"), True, "danger" if art == "fehler" else "primary")])


# --------------------------------------------------------------------------
# Nebenfenster
# --------------------------------------------------------------------------

class Nebenfenster:
    """Nicht-modales Fenster mit einer Karte, einem Textfeld und Schaltern."""

    def __init__(self, app, titel, breite=680, hoehe=540):
        tk = _tk
        self.app = app
        fenster = self.fenster = tk.Toplevel(app.master)
        fenster.withdraw()
        fenster.title(titel)
        faerben(fenster, bg="BG")
        s = app.skalierung
        self.groesse = (round(breite * s), round(hoehe * s))
        fenster.geometry("{}x{}".format(*self.groesse))
        fenster.minsize(round(420 * s), round(300 * s))
        self.karte = make_card(fenster, fill="both", expand=True, padx=12, pady=12)
        self.kopf = card_title(self.karte, titel)
        self.unterzeile = card_text(self.karte, "", wraplength=round((breite - 60) * s))
        self.leiste = faerben(tk.Frame(self.karte), bg="CARD")
        self.leiste.pack(side="bottom", fill="x", padx=14, pady=(8, 14))
        rahmen, self.text = textfeld(self.karte, hoehe=16, schrift=FONT_MONO_SMALL)
        rahmen.pack(fill="both", expand=True, padx=14)
        text_tags_faerben(self.text)
        GEFAERBTE_WIDGETS.append((self, None))
        FlatButton(self.leiste, _("Schließen"), fenster.destroy).pack(side="right")
        FlatButton(self.leiste, _("In die Zwischenablage kopieren"),
                   self.kopieren).pack(side="right", padx=(0, 8))
        fenster.bind("<Escape>", lambda _e: fenster.destroy())

    def neu_faerben(self):
        text_tags_faerben(self.text)

    def zeigen(self):
        fenster_zentrieren(self.fenster, self.app.master, *self.groesse)
        self.fenster.deiconify()
        self.fenster.lift()
        self.fenster.focus_set()

    def schreiben(self, text, tag=None):
        text_schreiben(self.text, text, tag, ans_ende=False)

    def kopieren(self):
        self.app.zwischenablage(self.text.get("1.0", "end").rstrip())


class AbhaengigkeitsFenster(Nebenfenster):
    """Abhaengigkeiten eines Scripts - geprueft gegen die gewaehlte Installation."""

    def __init__(self, app, eintrag):
        super().__init__(app, _("Abhängigkeiten: {name}").format(name=eintrag["name"]))
        self.eintrag = eintrag
        self.fehlende = []
        self.knopf_installieren = FlatButton(self.leiste, _("Fehlende installieren …"),
                                             self._installieren, kind="primary")
        self.knopf_installieren.pack(side="left")
        self.fuellen()
        self.zeigen()

    def fuellen(self):
        app = self.app
        analyse = app.script_analysieren(self.eintrag["path"])
        inst = app.ausfuehrende_installation()
        self.unterzeile.configure(text=_("Geprüft gegen: {python}").format(
            python=installation_titel(inst) if inst else _("keine Installation gefunden")))
        text_leeren(self.text)
        self.schreiben(_("Pfad: {pfad}").format(pfad=self.eintrag["path"]) + "\n\n", "leise")
        if analyse["datei_fehlt"]:
            self.schreiben(_("Die Datei wurde nicht gefunden.") + "\n", "fehler")
            self.knopf_installieren.pack_forget()
            return
        if analyse["syntaxfehler"]:
            zeile, meldung = analyse["syntaxfehler"]
            self.schreiben(_("Syntaxfehler in Zeile {zeile}: {meldung}").format(
                zeile=zeile, meldung=meldung) + "\n\n", "fehler")

        def abschnitt(titel, eintraege, tag, zeile_bilden):
            self.schreiben(f"{titel} ({len(eintraege)})\n", "kopf")
            if not eintraege:
                self.schreiben("  " + _("(keine)") + "\n\n", "leise")
                return
            for eintrag in eintraege:
                self.schreiben("  " + zeile_bilden(eintrag) + "\n", tag)
            self.schreiben("\n")

        def paketzeile(eintrag):
            modul, pakete = eintrag
            if not pakete:
                return "✓ " + modul + "  " + _("(ohne Paketdaten)")
            return "✓ " + modul + "  ←  " + ", ".join(f"{n} {v}" for n, v in pakete)

        if analyse["unbekannt"]:
            self.schreiben(_("Die Module dieser Installation sind noch nicht eingelesen.")
                           + "\n\n", "warn")
        abschnitt(_("Fehlende Module"), analyse["fehlt"], "fehler",
                  lambda e: "✗ " + e[0] + "   →  pip install " + e[1])
        abschnitt(_("Optionale Module (fehlen, werden aber abgefangen)"), analyse["optional"],
                  "warn", lambda e: "○ " + e[0] + "   →  pip install " + e[1])
        abschnitt(_("Installierte Module"), analyse["extern"], "ok", paketzeile)
        abschnitt(_("Lokale Module (neben dem Script)"), analyse["lokal"], "info",
                  lambda m: "✓ " + m)
        abschnitt(_("Standardbibliothek"), analyse["stdlib"], "leise", lambda m: "✓ " + m)
        self.fehlende = sorted({vorschlag for _m, vorschlag in analyse["fehlt"]})
        if self.fehlende:
            self.knopf_installieren.pack(side="left")
        else:
            self.knopf_installieren.pack_forget()

    def _installieren(self):
        if self.fehlende:
            self.app.installieren_anfragen(self.fehlende, self.app.ausfuehrender_schluessel())


class ModulInfoFenster(Nebenfenster):
    """pip show zu einem Modul, dazu Importnamen und Abhaengigkeiten."""

    def __init__(self, app, schluessel, name):
        super().__init__(app, _("Modul: {name}").format(name=name), breite=700, hoehe=560)
        self.schluessel = schluessel
        self.name = name
        inst = app.installation(schluessel)
        index = app.index(schluessel)
        installiert = bool(index and index.ist_installiert(name))
        self.unterzeile.configure(text=_("{python} – {status}").format(
            python=installation_titel(inst) if inst else "?",
            status=_("installiert") if installiert else _("fehlt")))
        if installiert:
            FlatButton(self.leiste, _("Deinstallieren …"),
                       lambda: app.deinstallieren_anfragen(name, schluessel),
                       kind="danger").pack(side="left")
            FlatButton(self.leiste, _("Aktualisieren (Upgrade)"),
                       lambda: app.installieren_anfragen([name], schluessel, upgrade=True)
                       ).pack(side="left", padx=(8, 0))
        else:
            FlatButton(self.leiste, _("Installieren …"),
                       lambda: app.installieren_anfragen([name], schluessel),
                       kind="primary").pack(side="left")

        if index and installiert:
            paket = index.pakete[kanon(name)]
            self.schreiben(_("Importnamen") + "\n", "kopf")
            self.schreiben("  " + (", ".join(paket.get("top", ())) or "–") + "\n\n")
            self.schreiben(_("Benötigt") + "\n", "kopf")
            for anforderung in paket.get("requires", ()) or ["–"]:
                vorhanden = anforderung == "–" or index.ist_installiert(anforderung)
                self.schreiben("  " + anforderung + ("" if vorhanden else "  ✗ " + _("fehlt"))
                               + "\n", None if vorhanden else "fehler")
            self.schreiben("\n" + _("Benötigt von") + "\n", "kopf")
            self.schreiben("  " + (", ".join(sorted(index.rueck.get(kanon(name), []),
                                                    key=str.lower)) or "–") + "\n\n")
            self.schreiben("pip show\n", "kopf")
            self.schreiben("  " + _("wird geladen …") + "\n", "leise")
            threading.Thread(target=self._pip_show, args=(inst["exe"],), daemon=True).start()
        else:
            self.schreiben(_("Dieses Modul ist in der gewählten Installation nicht vorhanden.")
                           + "\n\n", "warn")
            self.schreiben(_("Installieren lässt es sich über den Schalter unten oder in der "
                             "Konsole mit:") + "\n\n")
            self.schreiben(f'  "{inst["exe"] if inst else "python"}" -m pip install {name}\n',
                           "info")
        self.zeigen()

    def _pip_show(self, exe):
        try:
            _code, aus, fehler = verdeckt_ausfuehren(
                [exe, "-m", "pip", "show", "--disable-pip-version-check", self.name], timeout=60)
            text = aus or fehler
        except (OSError, subprocess.SubprocessError) as ausnahme:
            text = str(ausnahme)
        self.app.im_hauptthread(self._pip_show_zeigen, text)

    def _pip_show_zeigen(self, text):
        try:
            self.text.configure(state="normal")
            start = self.text.search(tr(_("wird geladen …")), "1.0", "end")
            if start:
                self.text.delete(f"{start} linestart", f"{start} lineend +1c")
            self.text.insert("end", "\n".join("  " + z for z in text.strip().splitlines()) + "\n")
            self.text.configure(state="disabled")
        except _tk.TclError:                 # Fenster ist schon geschlossen
            pass


class ZeitplanFenster:
    """Scripts in festen Abstaenden starten - und die Plaene wieder beenden."""

    def __init__(self, app):
        tk, ttk = _tk, _ttk
        self.app = app
        fenster = self.fenster = tk.Toplevel(app.master)
        fenster.withdraw()
        fenster.title(_("Zeitplan"))
        fenster.transient(app.master)
        faerben(fenster, bg="BG")
        karte = make_card(fenster, fill="both", expand=True, padx=12, pady=12)
        card_title(karte, _("Zeitplan"))
        card_text(karte, _("Startet ein Script wiederholt im gewählten Abstand, solange dieses "
                           "Programm läuft. Läuft das Script beim nächsten Termin noch, wird "
                           "dieser Termin übersprungen."),
                  wraplength=round(440 * app.skalierung))

        gitter = faerben(tk.Frame(karte), bg="CARD")
        gitter.pack(fill="x", padx=14, pady=(0, 8))
        gitter.columnconfigure(1, weight=1)
        beschriften(faerben(tk.Label(gitter, font=FONT_SMALL, anchor="w"), bg="CARD",
                            fg="MUTED"), _("Script")).grid(row=0, column=0, sticky="w")
        self.var_script = tk.StringVar()
        self.auswahl = ttk.Combobox(gitter, textvariable=self.var_script, state="readonly",
                                    font=FONT_SMALL,
                                    values=[s["name"] for s in app.cfg["scripts"]])
        self.auswahl.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=2)
        beschriften(faerben(tk.Label(gitter, font=FONT_SMALL, anchor="w"), bg="CARD",
                            fg="MUTED"), _("Abstand (Sekunden)")).grid(row=1, column=0,
                                                                        sticky="w")
        self.var_abstand = tk.StringVar(value="60")
        ttk.Entry(gitter, textvariable=self.var_abstand, font=FONT_SMALL, width=8).grid(
            row=1, column=1, sticky="w", padx=(10, 0), pady=2)
        FlatButton(gitter, _("Planen"), self._planen, kind="primary").grid(
            row=1, column=1, sticky="e", pady=2)

        card_title(karte, _("Aktive Pläne"))
        self.liste = faerben(tk.Listbox(karte, height=6, font=FONT_SMALL, relief="flat",
                                        highlightthickness=1, activestyle="none"),
                             bg="FIELD_BG", fg="TEXT", highlightbackground="BORDER",
                             highlightcolor="ACCENT", selectbackground="ACCENT",
                             selectforeground="ON_ACCENT")
        self.liste.pack(fill="both", expand=True, padx=14)
        leiste = faerben(tk.Frame(karte), bg="CARD")
        leiste.pack(fill="x", padx=14, pady=(8, 14))
        FlatButton(leiste, _("Schließen"), fenster.destroy).pack(side="right")
        FlatButton(leiste, _("Plan beenden"), self._beenden, kind="danger").pack(side="left")
        self._liste_fuellen()
        fenster.bind("<Escape>", lambda _e: fenster.destroy())
        fenster_zentrieren(fenster, app.master)
        fenster.deiconify()

    def _liste_fuellen(self):
        self.liste.delete(0, "end")
        self.plan_ids = []
        for plan_id, plan in self.app.zeitplaene.items():
            self.plan_ids.append(plan_id)
            self.liste.insert("end", tr(_("{name} – alle {sekunden} s").format(
                name=plan["eintrag"]["name"], sekunden=plan["sekunden"])))

    def _planen(self):
        name = self.var_script.get()
        eintrag = next((s for s in self.app.cfg["scripts"] if s["name"] == name), None)
        if not eintrag:
            melden(self.app, _("Zeitplan"), _("Bitte ein Script auswählen."))
            return
        try:
            sekunden = int(self.var_abstand.get())
            if sekunden < 5:
                raise ValueError
        except ValueError:
            melden(self.app, _("Zeitplan"), _("Der Abstand muss eine ganze Zahl ab 5 sein."),
                   art="fehler")
            return
        self.app.zeitplan_anlegen(eintrag, sekunden)
        self._liste_fuellen()

    def _beenden(self):
        auswahl = self.liste.curselection()
        if not auswahl:
            return
        self.app.zeitplan_beenden(self.plan_ids[auswahl[0]])
        self._liste_fuellen()


# --------------------------------------------------------------------------
# Hauptfenster
# --------------------------------------------------------------------------

ZEILEN_HOEHE = 40                    # Hoehe einer Script-Zeile bei 100 % Skalierung


class ManagerApp:
    """Hauptfenster mit den Reitern Scripts, Module und Info."""

    def __init__(self, master) -> None:
        self.master = master
        # Das Fenster bleibt verborgen, bis es fertig aufgebaut und an seinem
        # Platz ist - sonst sieht man es erst an der Standardposition.
        master.withdraw()

        self.cfg = load_config()
        self._einstellungen_vervollstaendigen()
        self.skalierung = max(1.0, master.winfo_fpixels("1i") / 96.0)
        self.zeilen_hoehe = round(ZEILEN_HOEHE * self.skalierung)

        self.aufgaben = queue.Queue()        # Auftraege anderer Threads an die Oberflaeche
        self.indizes = {}                    # Schluessel -> ModulIndex
        self.analysen = {}                   # Pfad -> (Stempel, Funde, Syntaxfehler)
        self.laeufe = {}                     # laufende Scripts
        self.lauf_nummer = 0
        self.fehlerprotokoll = []            # Fehlermeldungen beendeter Laeufe
        self.zeitplaene = {}
        self.plan_nummer = 0
        self.seite = 0
        self.pro_seite = 0                   # wird beim ersten Vermessen gesetzt
        self.einlesen_laeuft = False
        self.pip_laeuft = False
        self.modul_reiter_daten = {}         # Schluessel -> {"seite", "baum", "info"}
        self._status = None
        self._meldung = None                 # sichtbare Rueckmeldung (blendet sich aus)
        self._meldung_auftrag = None
        self._fenster_auftrag = None
        self._bereit = False

        master.title(PROGRAMM)
        master.configure(bg=BG)
        master.protocol("WM_DELETE_WINDOW", self.schliessen)

        self._variablen_anlegen()
        self._stil_setzen()
        self._aufbauen()
        self._fenster_platzieren()
        master.deiconify()
        if self.cfg.get("fenster", {}).get("max"):
            master.state("zoomed")
        master.after(40, self._aufgaben_abarbeiten)
        master.after(300, self._startbereit)
        self._beim_start_einlesen()

    # -- Einstellungen -----------------------------------------------------

    def _einstellungen_vervollstaendigen(self):
        cfg = self.cfg
        if not isinstance(cfg.get("scripts"), list):
            cfg["scripts"] = self._alte_scriptliste()
        cfg["scripts"] = [s for s in cfg["scripts"]
                          if isinstance(s, dict) and isinstance(s.get("path"), str)]
        for eintrag in cfg["scripts"]:
            eintrag["name"] = str(eintrag.get("name") or
                                  os.path.splitext(os.path.basename(eintrag["path"]))[0])
        if cfg.get("modul_aktualisierung") not in ("auto", "manuell"):
            cfg["modul_aktualisierung"] = "manuell"
        for schluessel, art in (("installationen", list), ("modul_daten", dict),
                                ("bekannte_module", dict), ("weitere_interpreter", list)):
            if not isinstance(cfg.get(schluessel), art):
                cfg[schluessel] = art()
        cfg["installationen"] = [i for i in cfg["installationen"]
                                 if isinstance(i, dict) and {"key", "exe", "version",
                                                             "ordner"} <= set(i)]

    @staticmethod
    def _alte_scriptliste():
        """Script-Liste der Vorgaengerfassung uebernehmen, falls vorhanden."""
        try:
            with open(os.path.join(programm_ordner(), ALTE_CONFIG), encoding="utf-8") as datei:
                alt = json.load(datei)
        except (OSError, ValueError):
            return []
        if not isinstance(alt, list):
            return []
        return [{"name": str(e.get("name") or ""), "path": e["path"]} for e in alt
                if isinstance(e, dict) and isinstance(e.get("path"), str)]

    def sichern(self):
        self.cfg["language"] = _.language
        self.cfg["theme"] = CURRENT_THEME
        if not save_config(self.cfg):
            self.meldung(_("Die Einstellungen konnten nicht gespeichert werden: {pfad}").format(
                pfad=config_path()), fehler=True)

    # -- Fenster ------------------------------------------------------------

    def _arbeitsflaeche(self, punkt=None):
        """Arbeitsbereich (x, y, Breite, Höhe) eines Monitors ohne Taskleiste.

        Ohne Punkt zaehlt der Monitor unter dem Mauszeiger, mit Punkt der, auf
        dem der Punkt liegt. Liegt er auf keinem - etwa weil ein zweiter
        Bildschirm abgezogen wurde -, ist die Antwort None.
        """
        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes

                class MONITORINFO(ctypes.Structure):
                    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                                ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]

                benutzer = ctypes.windll.user32
                stelle = wintypes.POINT()
                if punkt is None:
                    benutzer.GetCursorPos(ctypes.byref(stelle))
                    monitor = benutzer.MonitorFromPoint(stelle, 2)   # naechstgelegener
                else:
                    stelle.x, stelle.y = int(punkt[0]), int(punkt[1])
                    monitor = benutzer.MonitorFromPoint(stelle, 0)   # keiner, wenn daneben
                if not monitor:
                    return None
                info = MONITORINFO()
                info.cbSize = ctypes.sizeof(MONITORINFO)
                if benutzer.GetMonitorInfoW(monitor, ctypes.byref(info)):
                    r = info.rcWork
                    return r.left, r.top, r.right - r.left, r.bottom - r.top
            except (AttributeError, OSError, ValueError):
                pass
        breite, hoehe = self.master.winfo_screenwidth(), self.master.winfo_screenheight()
        if punkt is not None and not (0 <= punkt[0] < breite and 0 <= punkt[1] < hoehe):
            return None
        return 0, 0, breite, hoehe

    def _fenster_platzieren(self):
        """Beim ersten Start mittig, danach dort, wo das Fenster zuletzt war."""
        s = self.skalierung
        self.master.minsize(round(900 * s), round(560 * s))
        gespeichert = self.cfg.get("fenster")
        if isinstance(gespeichert, dict) and all(isinstance(gespeichert.get(k), int)
                                                 for k in ("x", "y", "w", "h")):
            bereich = self._arbeitsflaeche((gespeichert["x"] + 40, gespeichert["y"] + 20))
            if bereich:
                rx, ry, pb, ph = bereich
                breite, hoehe = min(gespeichert["w"], pb), min(gespeichert["h"], ph)
                x = max(rx, min(gespeichert["x"], rx + pb - breite))
                y = max(ry, min(gespeichert["y"], ry + ph - hoehe))
                self.master.geometry(f"{breite}x{hoehe}+{x}+{y}")
                return
        rx, ry, pb, ph = self._arbeitsflaeche()
        breite = min(round(1280 * s), pb - 40)
        hoehe = min(round(820 * s), ph - 40)
        self.master.geometry(f"{breite}x{hoehe}+{rx + (pb - breite) // 2}"
                             f"+{ry + (ph - hoehe) // 2}")

    def _startbereit(self):
        self._bereit = True
        self.master.bind("<Configure>", self._fenster_bewegt, add="+")

    def _fenster_bewegt(self, ereignis):
        """Lage und Groesse merken, sobald das Fenster eine Weile ruht."""
        if ereignis.widget is not self.master or not self._bereit:
            return
        if self._fenster_auftrag is not None:
            self.master.after_cancel(self._fenster_auftrag)
        self._fenster_auftrag = self.master.after(700, self._fensterlage_sichern)

    def _fensterlage_sichern(self):
        self._fenster_auftrag = None
        zustand = self.master.state()
        if zustand in ("iconic", "withdrawn"):
            return                           # minimiert: Lage waere -32000
        maximiert = zustand == "zoomed"
        alt = self.cfg.get("fenster") if isinstance(self.cfg.get("fenster"), dict) else {}
        if maximiert:
            neu = dict(alt, max=True)        # Lage vor dem Maximieren behalten
        else:
            neu = {"x": self.master.winfo_x(), "y": self.master.winfo_y(),
                   "w": self.master.winfo_width(), "h": self.master.winfo_height(),
                   "max": False}
        if neu != alt:
            self.cfg["fenster"] = neu
            self.sichern()

    # -- Threads -------------------------------------------------------------

    def im_hauptthread(self, funktion, *argumente):
        """Auftrag aus einem anderen Thread an die Oberflaeche uebergeben.

        Tkinter darf nur vom Hauptthread aus angefasst werden; alles andere
        fuehrt frueher oder spaeter zu Abstuerzen ohne Meldung.
        """
        self.aufgaben.put((funktion, argumente))

    def _aufgaben_abarbeiten(self):
        try:
            for _runde in range(400):
                funktion, argumente = self.aufgaben.get_nowait()
                try:
                    funktion(*argumente)
                except _tk.TclError:
                    pass                     # Fenster wurde inzwischen geschlossen
                except Exception as fehler:  # noqa: BLE001 - die Schleife muss weiterlaufen
                    self.meldung(_("Interner Fehler: {fehler}").format(fehler=fehler),
                                 fehler=True)
        except queue.Empty:
            pass
        self.master.after(40, self._aufgaben_abarbeiten)

    # -- Stil -----------------------------------------------------------------

    def _variablen_anlegen(self):
        tk = _tk
        self.var_status = tk.StringVar(value="")
        self.var_stand = tk.StringVar(value="")
        self.var_seite = tk.StringVar(value="")
        self.var_suche = tk.StringVar(value="")
        self.var_dunkel = tk.BooleanVar(value=CURRENT_THEME == "dark")
        self.var_suche.trace_add("write", lambda *_a: self._suche_geaendert())

    def _stil_setzen(self) -> None:
        """ttk-Bedienelemente an das gewählte Farbschema anpassen."""
        tk, ttk = _tk, _ttk
        stil = ttk.Style()
        try:
            if stil.theme_use() != "clam":
                stil.theme_use("clam")
        except tk.TclError:
            pass

        for widget in ("TEntry", "TCombobox"):
            # lightcolor/darkcolor sind die 3D-Kanten des clam-Themes - ohne
            # sie zeichnet Tk im dunklen Schema weisse Raender um die Felder
            stil.configure(widget, fieldbackground=FIELD_BG, foreground=TEXT,
                           background=BTN_BG, bordercolor=BORDER,
                           lightcolor=BORDER, darkcolor=BORDER,
                           arrowcolor=TEXT, insertcolor=TEXT, padding=3)
            stil.map(widget,
                     fieldbackground=[("readonly", FIELD_BG), ("disabled", BG)],
                     background=[("readonly", BTN_BG), ("active", BTN_HOVER)],
                     foreground=[("readonly", TEXT), ("disabled", BTN_DISABLED)],
                     bordercolor=[("focus", ACCENT)],
                     lightcolor=[("focus", ACCENT)],
                     darkcolor=[("focus", ACCENT)])

        self.master.option_add("*TCombobox*Listbox.background", FIELD_BG)
        self.master.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.master.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.master.option_add("*TCombobox*Listbox.selectForeground", ON_ACCENT)

        # lightcolor/darkcolor zeichnen den Rahmen um den Reiterinhalt
        stil.configure("TNotebook", background=BG, bordercolor=BORDER, borderwidth=0,
                       lightcolor=BORDER, darkcolor=BORDER)
        stil.configure("TNotebook.Tab", background=TAB_BG, foreground=MUTED,
                       bordercolor=BORDER, lightcolor=TAB_BG, darkcolor=TAB_BG,
                       padding=(16, 8), font=FONT_SMALL)
        stil.map("TNotebook.Tab",
                 background=[("selected", CARD), ("active", BTN_HOVER)],
                 foreground=[("selected", TEXT)],
                 lightcolor=[("selected", CARD)],
                 darkcolor=[("selected", CARD)])
        stil.configure("Innen.TNotebook", background=CARD, bordercolor=BORDER, borderwidth=0,
                       lightcolor=BORDER, darkcolor=BORDER)
        stil.configure("Innen.TNotebook.Tab", padding=(12, 5))

        stil.configure("Treeview", background=FIELD_BG, fieldbackground=FIELD_BG,
                       foreground=TEXT, bordercolor=BORDER, lightcolor=FIELD_BG,
                       darkcolor=FIELD_BG, font=FONT_SMALL,
                       rowheight=round(24 * self.skalierung))
        stil.map("Treeview", background=[("selected", ACCENT)],
                 foreground=[("selected", ON_ACCENT)])
        stil.configure("Treeview.Heading", background=BTN_BG, foreground=TEXT,
                       bordercolor=BORDER, lightcolor=BTN_BG, darkcolor=BTN_BG,
                       font=("Segoe UI", 9, "bold"), padding=(6, 4))
        stil.map("Treeview.Heading", background=[("active", BTN_HOVER)])
        for richtung in ("Vertical", "Horizontal"):
            stil.configure(f"{richtung}.TScrollbar", background=BTN_BG, troughcolor=TROUGH,
                           bordercolor=BORDER, arrowcolor=TEXT, lightcolor=BTN_BG,
                           darkcolor=BTN_BG, gripcount=0)
            stil.map(f"{richtung}.TScrollbar", background=[("active", BTN_HOVER)])

    # -- Aufbau ---------------------------------------------------------------

    def _aufbauen(self) -> None:
        tk, ttk = _tk, _ttk
        GEFAERBTE_WIDGETS.clear()
        BESCHRIFTUNGEN.clear()
        self.aussen = faerben(tk.Frame(self.master), bg="BG")
        self.aussen.pack(fill="both", expand=True)

        self._kopfzeile_bauen(self.aussen)
        self._statusleiste_bauen(self.aussen)

        self.reiter = ttk.Notebook(self.aussen)
        self.reiter.pack(fill="both", expand=True, padx=16, pady=(12, 8))
        for titel, bauen in ((_("Scripts"), self._seite_scripts_bauen),
                             (_("Module"), self._seite_module_bauen),
                             (_("Info & Copyright"), self._seite_info_bauen)):
            seite = faerben(tk.Frame(self.reiter), bg="BG")
            self.reiter.add(seite)
            beschriftung_merken(lambda neu, s=seite: self.reiter.tab(s, text=f"  {neu}  "), titel)
            bauen(seite)
        self.reiter.select(min(2, max(0, int(self.cfg.get("reiter", 0) or 0))))
        self.reiter.bind("<<NotebookTabChanged>>", self._reiter_gewechselt)
        self.status(_("Bereit."))

    def _reiter_gewechselt(self, _ereignis=None):
        self.cfg["reiter"] = self.reiter.index("current")

    def _kopfzeile_bauen(self, eltern) -> None:
        tk, ttk = _tk, _ttk
        kopf = faerben(tk.Frame(eltern), bg="HEADER")
        kopf.pack(fill="x")

        marke = faerben(tk.Frame(kopf), bg="HEADER")
        marke.pack(side="left", padx=18, pady=12)
        faerben(tk.Label(marke, text=PROGRAMM, font=("Segoe UI", 15, "bold"), anchor="w"),
                bg="HEADER", fg="HEADER_TITLE").pack(fill="x")
        beschriften(faerben(tk.Label(marke, font=FONT_TINY, anchor="w"),
                            bg="HEADER", fg="HEADER_GROUP"),
                    _("Version {version}").format(version=VERSION)).pack(fill="x")

        umschalter = faerben(tk.Frame(kopf), bg="HEADER")
        umschalter.pack(side="right", padx=18)
        beschriften(faerben(tk.Label(umschalter, font=("Segoe UI", 8, "bold"), anchor="e"),
                            bg="HEADER", fg="HEADER_GROUP"),
                    _("Sprache & Darstellung")).pack(fill="x", pady=(10, 2))
        zeile = faerben(tk.Frame(umschalter), bg="HEADER")
        zeile.pack(fill="x", pady=(0, 10))
        self.sprachnamen = _.available()
        self.sprachfeld = ttk.Combobox(zeile, state="readonly", font=FONT_SMALL, width=12,
                                       values=list(self.sprachnamen.values()))
        self.sprachfeld.set(self.sprachnamen[_.language])
        self.sprachfeld.pack(side="left")
        self.sprachfeld.bind("<<ComboboxSelected>>", self._sprache_gewaehlt)
        beschriften(faerben(tk.Checkbutton(zeile, variable=self.var_dunkel,
                                           command=self._schema_umgeschaltet, font=FONT_SMALL,
                                           highlightthickness=0, bd=0, cursor="hand2"),
                            bg="HEADER", fg="HEADER_TEXT", activebackground="HEADER",
                            activeforeground="HEADER_TITLE", selectcolor="HEADER_HOVER"),
                    _("Dunkel")).pack(side="left", padx=(8, 0))

    def _statusleiste_bauen(self, eltern) -> None:
        tk = _tk
        leiste = faerben(tk.Frame(eltern), bg="STATUS_BG")
        leiste.pack(side="bottom", fill="x")
        faerben(tk.Label(leiste, textvariable=self.var_status, font=FONT_SMALL, anchor="w"),
                bg="STATUS_BG", fg="MUTED").pack(side="left", padx=14, pady=4)
        faerben(tk.Label(leiste, textvariable=self.var_stand, font=FONT_TINY, anchor="e"),
                bg="STATUS_BG", fg="MUTED").pack(side="right", padx=(0, 14))

    # -- Reiter 1: Scripts ------------------------------------------------------

    def _seite_scripts_bauen(self, eltern) -> None:
        tk, ttk = _tk, _ttk
        raster = faerben(tk.Frame(eltern), bg="BG")
        raster.pack(fill="both", expand=True, padx=14, pady=14)
        raster.columnconfigure(0, weight=2, uniform="spalten")
        raster.columnconfigure(1, weight=3, uniform="spalten")
        raster.rowconfigure(0, weight=1)

        # --- Script-Liste ---
        links = make_card(raster)
        links.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        card_title(links, _("Python-Scripts"))

        werkzeuge = faerben(tk.Frame(links), bg="CARD")
        werkzeuge.pack(fill="x", padx=14, pady=(0, 8))
        FlatButton(werkzeuge, _("Script hinzufügen"), self.script_hinzufuegen,
                   kind="primary").pack(side="left")
        FlatButton(werkzeuge, _("Abhängigkeiten prüfen"), self.abhaengigkeiten_neu_pruefen,
                   tooltip=_("Liest die Importe aller Scripts neu ein und prüft sie gegen "
                             "die gewählte Installation.")).pack(side="left", padx=(8, 0))
        FlatButton(werkzeuge, _("Zeitplan"), lambda: ZeitplanFenster(self)).pack(
            side="left", padx=(8, 0))

        python_zeile = faerben(tk.Frame(links), bg="CARD")
        python_zeile.pack(fill="x", padx=14, pady=(0, 10))
        beschriften(faerben(tk.Label(python_zeile, font=FONT_SMALL, anchor="w"),
                            bg="CARD", fg="MUTED"), _("Ausführen mit")).pack(side="left")
        self.python_feld = ttk.Combobox(python_zeile, state="readonly", font=FONT_SMALL)
        self.python_feld.pack(side="left", fill="x", expand=True, padx=(10, 0))
        self.python_feld.bind("<<ComboboxSelected>>", self._python_gewaehlt)

        # Die Liste blaettert statt zu rollen: Es passen so viele Zeilen auf
        # eine Seite, wie die Hoehe hergibt; der Rest landet auf Folgeseiten.
        blaettern = faerben(tk.Frame(links), bg="CARD")
        blaettern.pack(side="bottom", fill="x", padx=14, pady=(4, 12))
        self.knopf_zurueck = IconKnopf(blaettern, "zurueck", lambda: self.blaettern(-1),
                                       _("Vorherige Seite"), grund="CARD")
        self.knopf_zurueck.pack(side="left")
        self.knopf_weiter = IconKnopf(blaettern, "weiter", lambda: self.blaettern(1),
                                      _("Nächste Seite"), grund="CARD")
        self.knopf_weiter.pack(side="right")
        faerben(tk.Label(blaettern, textvariable=self.var_seite, font=FONT_SMALL),
                bg="CARD", fg="MUTED").pack(side="left", fill="x", expand=True)

        self.liste_rahmen = faerben(tk.Frame(links), bg="CARD")
        self.liste_rahmen.pack(fill="both", expand=True, padx=14)
        self.liste_rahmen.pack_propagate(False)
        self.liste_rahmen.bind("<Configure>", self._liste_vermessen)
        self._mausrad_binden(self.liste_rahmen)

        # --- Ausgabe ---
        rechts = make_card(raster)
        rechts.grid(row=0, column=1, sticky="nsew")
        kopf = faerben(tk.Frame(rechts), bg="CARD")
        kopf.pack(fill="x", padx=14, pady=(12, 6))
        card_title(kopf, _("Script-Ausgabe"), side="left")
        self.knopf_stopp = FlatButton(kopf, _("Stoppen"), self.scripts_stoppen, state="disabled",
                                      tooltip=_("Beendet alle laufenden Scripts."))
        self.knopf_stopp.pack(side="right")
        FlatButton(kopf, _("Leeren"), self.ausgabe_leeren).pack(side="right", padx=(0, 8))
        self.knopf_fehler = FlatButton(
            kopf, _("Fehlermeldungen kopieren"), self.fehler_kopieren, state="disabled",
            tooltip=_("Legt alle Fehlermeldungen seit dem letzten Leeren in die "
                      "Zwischenablage."))
        self.knopf_fehler.pack(side="right", padx=(0, 8))

        rahmen, self.ausgabe = textfeld(rechts, hoehe=20, schrift=FONT_MONO_SMALL)
        rahmen.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.ausgabe.configure(wrap="char")
        text_tags_faerben(self.ausgabe)
        self._kontextmenue_text(self.ausgabe, mit_fehlern=True)

        self._python_feld_fuellen()

    def _mausrad_binden(self, widget):
        widget.bind("<MouseWheel>", self._mausrad, add="+")

    def _mausrad(self, ereignis):
        self.blaettern(-1 if ereignis.delta > 0 else 1)
        return "break"

    def _liste_vermessen(self, _ereignis=None):
        hoehe = self.liste_rahmen.winfo_height()
        if hoehe < 10:
            return
        pro_seite = max(1, hoehe // self.zeilen_hoehe)
        if pro_seite != self.pro_seite:
            erster = self.seite * self.pro_seite         # erste sichtbare Zeile bleibt sichtbar
            self.pro_seite = pro_seite
            self.seite = erster // pro_seite
            self.liste_zeichnen()

    def seitenzahl(self) -> int:
        return max(1, math.ceil(len(self.cfg["scripts"]) / max(1, self.pro_seite)))

    def blaettern(self, schritt):
        neu = max(0, min(self.seitenzahl() - 1, self.seite + schritt))
        if neu != self.seite:
            self.seite = neu
            self.liste_zeichnen()

    def liste_zeichnen(self):
        """Die Zeilen der aktuellen Seite neu aufbauen."""
        tk = _tk
        for kind in self.liste_rahmen.winfo_children():
            kind.destroy()
        scripts = self.cfg["scripts"]
        seiten = self.seitenzahl()
        self.seite = max(0, min(self.seite, seiten - 1))
        if not scripts:
            faerben(tk.Label(self.liste_rahmen, font=FONT_SMALL, justify="left", anchor="nw",
                             wraplength=round(360 * self.skalierung),
                             text=_("Noch keine Scripts – „Script hinzufügen“ nimmt das "
                                    "erste auf.")),
                    bg="CARD", fg="MUTED").pack(fill="x", pady=8)
        erster = self.seite * max(1, self.pro_seite)
        for nummer, eintrag in enumerate(scripts[erster:erster + max(1, self.pro_seite)],
                                       start=erster):
            self._zeile_bauen(nummer, eintrag)
        self.var_seite.set(_("Seite {seite} von {seiten} · {anzahl} Scripts").format(
            seite=self.seite + 1, seiten=seiten, anzahl=len(scripts)))
        self.knopf_zurueck.configure(state="normal" if self.seite > 0 else "disabled")
        self.knopf_weiter.configure(state="normal" if self.seite < seiten - 1 else "disabled")

    def _zeile_bauen(self, nummer, eintrag):
        tk = _tk
        palette = THEMES[CURRENT_THEME]
        zeile = tk.Frame(self.liste_rahmen, height=self.zeilen_hoehe - round(6 * self.skalierung),
                         bg=palette["CARD_ALT"], highlightthickness=1,
                         highlightbackground=palette["BORDER"])
        zeile.pack(fill="x", pady=(0, round(6 * self.skalierung)))
        zeile.pack_propagate(False)

        zustand = self.script_zustand(eintrag)
        rolle = {"ok": "OK", "warn": "WARN", "fehlt": "DANGER"}.get(zustand, "MUTED")
        punkt = tk.Label(zeile, text="●", font=FONT_SMALL, bg=palette["CARD_ALT"],
                         fg=palette[rolle])
        punkt.pack(side="left", padx=(10, 6))

        for icon, befehl, hinweis, hover in (
                ("entfernen", lambda: self.script_entfernen(nummer), _("Script entfernen"),
                 "DANGER"),
                ("abhaengig", lambda: AbhaengigkeitsFenster(self, eintrag),
                 _("Abhängigkeiten anzeigen"), "ACCENT"),
                ("umbenennen", lambda: self.script_umbenennen(nummer), _("Namen bearbeiten"),
                 "ACCENT"),
                ("start", lambda: self.script_starten(eintrag), _("Script starten"), "OK")):
            knopf = IconKnopf(zeile, icon, befehl, hinweis, hover_rolle=hover)
            knopf.pack(side="right", padx=(0, 2) if icon != "entfernen" else (0, 6))
            self._mausrad_binden(knopf)

        name = tk.Label(zeile, text=eintrag["name"], font=FONT, anchor="w",
                        bg=palette["CARD_ALT"], fg=palette["TEXT"])
        name.pack(side="left", fill="x", expand=True)
        name.bind("<Double-Button-1>", lambda _e: self.script_starten(eintrag))
        Tooltip(name, lambda: self.script_tooltip(eintrag),
                warnung=lambda: self.script_zustand(eintrag) in ("warn", "fehlt"))
        Tooltip(punkt, lambda: self.script_tooltip(eintrag),
                warnung=lambda: self.script_zustand(eintrag) in ("warn", "fehlt"))
        for widget in (zeile, punkt, name):
            self._mausrad_binden(widget)

    # -- Scripts verwalten -------------------------------------------------------

    def script_hinzufuegen(self):
        from tkinter import filedialog
        pfad = filedialog.askopenfilename(
            parent=self.master, title=tr(_("Script hinzufügen")),
            filetypes=[(tr(_("Python-Scripts")), "*.py *.pyw"), (tr(_("Alle Dateien")), "*.*")])
        if not pfad:
            return
        pfad = os.path.normpath(pfad)
        if any(os.path.normcase(s["path"]) == os.path.normcase(pfad)
               for s in self.cfg["scripts"]):
            melden(self, _("Script hinzufügen"), _("Dieses Script steht schon in der Liste."))
            return
        vorgabe = os.path.splitext(os.path.basename(pfad))[0]
        dialog = Dialog(self, _("Script hinzufügen"),
                        _("Unter welchem Namen soll das Script in der Liste stehen?"),
                        [(_("Abbrechen"), None, "secondary"), (_("Hinzufügen"), True, "primary")],
                        eingabe=vorgabe)
        if not dialog.ergebnis:
            return
        self.cfg["scripts"].append({"name": dialog.eingabe_text or vorgabe, "path": pfad})
        self.sichern()
        self.seite = self.seitenzahl() - 1           # neue Zeile gleich zeigen
        self.liste_zeichnen()
        self._modul_baum_fuellen(self.ausfuehrender_schluessel())
        self.meldung(_("„{name}“ hinzugefügt.").format(name=dialog.eingabe_text or vorgabe))

    def script_umbenennen(self, nummer):
        eintrag = self.cfg["scripts"][nummer]
        dialog = Dialog(self, _("Namen bearbeiten"), _("Neuer Name für „{name}“:").format(
            name=eintrag["name"]),
            [(_("Abbrechen"), None, "secondary"), (_("Übernehmen"), True, "primary")],
            eingabe=eintrag["name"])
        if dialog.ergebnis and dialog.eingabe_text:
            eintrag["name"] = dialog.eingabe_text
            self.sichern()
            self.liste_zeichnen()

    def script_entfernen(self, nummer):
        eintrag = self.cfg["scripts"][nummer]
        dialog = Dialog(self, _("Script entfernen"),
                        _("„{name}“ aus der Liste entfernen? Die Datei selbst bleibt "
                          "unangetastet.").format(name=eintrag["name"]),
                        [(_("Abbrechen"), None, "secondary"), (_("Entfernen"), True, "danger")])
        if dialog.ergebnis:
            del self.cfg["scripts"][nummer]
            self.sichern()
            self.liste_zeichnen()
            self._modul_baum_fuellen(self.ausfuehrender_schluessel())

    def abhaengigkeiten_neu_pruefen(self):
        self.analysen.clear()
        self.liste_zeichnen()
        self._modul_baum_fuellen(self.ausfuehrender_schluessel())
        self.meldung(_("Abhängigkeiten aller Scripts neu geprüft."))

    # -- Abhaengigkeiten -----------------------------------------------------------

    def script_analysieren(self, pfad):
        """Importe des Scripts gegen die ausfuehrende Installation pruefen.

        Die Importe selbst werden nur neu gelesen, wenn sich die Datei
        geaendert hat.
        """
        ergebnis = {"datei_fehlt": False, "syntaxfehler": None, "stdlib": [], "extern": [],
                    "lokal": [], "fehlt": [], "optional": [], "unbekannt": []}
        try:
            info = os.stat(pfad)
        except OSError:
            ergebnis["datei_fehlt"] = True
            return ergebnis
        stempel = (info.st_mtime_ns, info.st_size)
        gemerkt = self.analysen.get(pfad)
        if gemerkt and gemerkt[0] == stempel:
            funde, syntaxfehler = gemerkt[1], gemerkt[2]
        else:
            try:
                funde, syntaxfehler = importe_lesen(pfad)
            except OSError:
                ergebnis["datei_fehlt"] = True
                return ergebnis
            self.analysen[pfad] = (stempel, funde, syntaxfehler)
        ergebnis["syntaxfehler"] = syntaxfehler
        schluessel = self.ausfuehrender_schluessel()
        weitere = [self.index(i["key"]) for i in self.installationen() if i["key"] != schluessel]
        ergebnis.update(abhaengigkeiten_pruefen(pfad, funde, self.index(schluessel),
                                                [w for w in weitere if w]))
        return ergebnis

    def script_zustand(self, eintrag):
        """ok, warn (fehlende Module / Syntaxfehler), fehlt (Datei) oder unbekannt."""
        analyse = self.script_analysieren(eintrag["path"])
        if analyse["datei_fehlt"]:
            return "fehlt"
        if analyse["fehlt"] or analyse["syntaxfehler"]:
            return "warn"
        if analyse["unbekannt"]:
            return "unbekannt"
        return "ok"

    def script_tooltip(self, eintrag):
        analyse = self.script_analysieren(eintrag["path"])
        zeilen = [tr(_("Pfad: {pfad}").format(pfad=eintrag["path"]))]
        if analyse["datei_fehlt"]:
            zeilen.append(tr(_("Die Datei wurde nicht gefunden.")))
            return "\n".join(zeilen)
        inst = self.ausfuehrende_installation()
        if inst:
            zeilen.append(tr(_("Geprüft gegen: {python}").format(python=installation_titel(inst))))
        zeilen.append("─" * 44)
        if analyse["syntaxfehler"]:
            zeile, meldung = analyse["syntaxfehler"]
            zeilen.append(tr(_("Syntaxfehler in Zeile {zeile}: {meldung}").format(
                zeile=zeile, meldung=meldung)))

        def block(titel, namen):
            if not namen:
                return
            zeilen.append("")
            zeilen.append(f"{tr(titel)} ({len(namen)}):")
            for name in namen[:5]:
                zeilen.append(f"  • {name}")
            if len(namen) > 5:
                zeilen.append("  " + tr(_("… und {anzahl} weitere").format(
                    anzahl=len(namen) - 5)))

        block(_("Standardbibliothek"), analyse["stdlib"])
        block(_("Installierte Module"), [m for m, _p in analyse["extern"]])
        block(_("Lokale Module"), analyse["lokal"])
        if analyse["fehlt"]:
            zeilen.append("")
            zeilen.append(tr(_("FEHLEND ({anzahl}):").format(anzahl=len(analyse["fehlt"]))))
            for modul, vorschlag in analyse["fehlt"]:
                zeilen.append(f"  ✗ {modul}   →  pip install {vorschlag}")
        if analyse["optional"]:
            block(_("Optional, nicht vorhanden"), [m for m, _v in analyse["optional"]])
        zeilen.append("")
        if analyse["unbekannt"]:
            zeilen.append(tr(_("Die Module dieser Installation sind noch nicht eingelesen.")))
        elif analyse["fehlt"]:
            zeilen.append(tr(_("Fehlende Module lassen sich über „Abhängigkeiten anzeigen“ "
                               "oder im Reiter „Module“ installieren.")))
        elif not (analyse["stdlib"] or analyse["extern"] or analyse["lokal"]):
            zeilen.append(tr(_("Keine Importe gefunden.")))
        else:
            zeilen.append(tr(_("Alle Abhängigkeiten sind vorhanden.")))
        zeilen.append(tr(_("Doppelklick auf den Namen startet das Script.")))
        return "\n".join(zeilen)

    def fehlende_fuer_scripts(self):
        """pip-Name -> Scripts, die das Modul brauchen und bei denen es fehlt."""
        fehlend = {}
        for eintrag in self.cfg["scripts"]:
            for _modul, vorschlag in self.script_analysieren(eintrag["path"])["fehlt"]:
                fehlend.setdefault(vorschlag, []).append(eintrag["name"])
        return fehlend

    def scripts_mit_paket(self, name):
        """Scripts, die in der ausfuehrenden Installation dieses Paket importieren."""
        gesucht = kanon(name)
        treffer = []
        for eintrag in self.cfg["scripts"]:
            for _modul, pakete in self.script_analysieren(eintrag["path"])["extern"]:
                if any(kanon(p) == gesucht for p, _v in pakete):
                    treffer.append(eintrag["name"])
                    break
        return treffer

    # -- Scripts ausfuehren -------------------------------------------------------

    def script_starten(self, eintrag):
        pfad = eintrag["path"]
        name = eintrag["name"]
        jetzt = datetime.now().strftime("%H:%M:%S")
        if not os.path.isfile(pfad):
            text_schreiben(self.ausgabe, f"\n[{jetzt}] " + tr(_("Datei nicht gefunden: {pfad}")
                                                              .format(pfad=pfad)) + "\n", "fehler")
            self.fehlerprotokoll.append(f"[{jetzt}] {name}\n" + tr(
                _("Datei nicht gefunden: {pfad}").format(pfad=pfad)))
            self._fehlerknopf_auffrischen()
            return
        inst = self.ausfuehrende_installation()
        exe = inst["exe"] if inst else (None if ist_eingefroren()
                                        else konsolen_python(sys.executable))
        if not exe:
            melden(self, _("Script starten"), _("Es wurde keine Python-Installation gefunden."),
                   art="fehler")
            return
        try:
            prozess = subprocess.Popen(
                [exe, "-u", pfad], cwd=os.path.dirname(pfad) or None, env=utf8_umgebung(),
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
                creationflags=OHNE_FENSTER)
        except OSError as fehler:
            text_schreiben(self.ausgabe, f"\n[{jetzt}] {name}: {fehler}\n", "fehler")
            self.fehlerprotokoll.append(f"[{jetzt}] {name}\n{fehler}")
            self._fehlerknopf_auffrischen()
            return

        self.lauf_nummer += 1
        lauf = {"nummer": self.lauf_nummer, "name": name, "pfad": pfad, "prozess": prozess,
                "fehler": [], "start": time.monotonic(), "uhrzeit": jetzt,
                "python": installation_titel(inst) if inst else exe}
        self.laeufe[lauf["nummer"]] = lauf
        text_schreiben(self.ausgabe, "\n" + "═" * 72 + "\n", "info")
        text_schreiben(self.ausgabe, f"[{jetzt}] " + tr(_("Start: {name}").format(name=name))
                       + f"   ({lauf['python']})\n", "info")
        text_schreiben(self.ausgabe, f"{pfad}\n", "leise")
        text_schreiben(self.ausgabe, "═" * 72 + "\n", "info")
        self._laufanzeige_auffrischen()

        leser = [threading.Thread(target=self._strom_lesen, args=(lauf, strom, art), daemon=True)
                 for strom, art in ((prozess.stdout, "aus"), (prozess.stderr, "fehler"))]
        for faden in leser:
            faden.start()

        def warten():
            prozess.wait()
            for faden in leser:
                faden.join(timeout=5)
            self.im_hauptthread(self._lauf_beendet, lauf)
        threading.Thread(target=warten, daemon=True).start()

    def _strom_lesen(self, lauf, strom, art):
        """Ausgabe zeilenweise lesen - stdout und stderr in eigenen Threads.

        Wuerde man erst stdout und danach stderr lesen, bliebe das Script
        haengen, sobald es mehr Fehlerausgabe erzeugt, als der Puffer fasst.
        """
        try:
            for zeile in iter(strom.readline, ""):
                self.im_hauptthread(self._ausgabe_zeile, lauf, zeile, art)
        except (OSError, ValueError):
            pass
        finally:
            try:
                strom.close()
            except OSError:
                pass

    def _ausgabe_zeile(self, lauf, zeile, art):
        praefix = f"[{lauf['name']}] " if len(self.laeufe) > 1 else ""
        if art == "fehler":
            lauf["fehler"].append(zeile)
            text_schreiben(self.ausgabe, praefix + zeile, "fehler")
            self._fehlerknopf_auffrischen()
        else:
            text_schreiben(self.ausgabe, praefix + zeile)

    def _lauf_beendet(self, lauf):
        self.laeufe.pop(lauf["nummer"], None)
        code = lauf["prozess"].returncode
        dauer = time.monotonic() - lauf["start"]
        jetzt = datetime.now().strftime("%H:%M:%S")
        text = tr(_("Beendet: {name} – Exit-Code {code} nach {dauer} s").format(
            name=lauf["name"], code=code, dauer=f"{dauer:.1f}"))
        if lauf.get("gestoppt"):
            text += " " + tr(_("(gestoppt)"))
        text_schreiben(self.ausgabe, f"\n[{jetzt}] {text}\n", "fehler" if code else "ok")
        if lauf["fehler"] or (code and not lauf.get("gestoppt")):
            block = [f"[{lauf['uhrzeit']}] {lauf['name']}", lauf["pfad"], lauf["python"], ""]
            block += [z.rstrip("\n") for z in lauf["fehler"]]
            block.append(f"Exit-Code {code}")
            self.fehlerprotokoll.append("\n".join(block))
        self._fehlerknopf_auffrischen()
        self._laufanzeige_auffrischen()

    def _laufanzeige_auffrischen(self):
        anzahl = len(self.laeufe)
        self.knopf_stopp.configure(state="normal" if anzahl else "disabled")
        self.knopf_stopp.art_setzen("danger" if anzahl else "secondary")
        if anzahl:
            self.status(_("{anzahl} Script(s) laufen.").format(anzahl=anzahl), verlauf=True)
        else:
            self.status(_("Bereit."))

    def _fehlerknopf_auffrischen(self):
        vorhanden = bool(self.fehlerprotokoll
                         or any(lauf["fehler"] for lauf in self.laeufe.values()))
        self.knopf_fehler.configure(state="normal" if vorhanden else "disabled")
        self.knopf_fehler.art_setzen("danger" if vorhanden else "secondary")

    def fehler_kopieren(self):
        bloecke = list(self.fehlerprotokoll)
        for lauf in self.laeufe.values():             # auch noch laufende Scripts
            if lauf["fehler"]:
                bloecke.append("\n".join([f"[{lauf['uhrzeit']}] {lauf['name']}", lauf["pfad"],
                                          lauf["python"], ""]
                                         + [z.rstrip("\n") for z in lauf["fehler"]]))
        if not bloecke:
            return
        self.zwischenablage(("\n\n" + "-" * 60 + "\n\n").join(bloecke))
        self.meldung(_("Fehlermeldungen in die Zwischenablage kopiert."))

    def ausgabe_leeren(self):
        text_leeren(self.ausgabe)
        self.fehlerprotokoll.clear()
        for lauf in self.laeufe.values():
            lauf["fehler"].clear()
        self._fehlerknopf_auffrischen()

    def scripts_stoppen(self):
        for lauf in list(self.laeufe.values()):
            lauf["gestoppt"] = True
            prozess = lauf["prozess"]
            try:
                prozess.terminate()
            except OSError:
                continue

            def notfalls_toeten(p=prozess):
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    try:
                        p.kill()
                    except OSError:
                        pass
            threading.Thread(target=notfalls_toeten, daemon=True).start()
        text_schreiben(self.ausgabe, "\n" + tr(_("[Stopp angefordert]")) + "\n", "warn")

    def zwischenablage(self, text):
        self.master.clipboard_clear()
        self.master.clipboard_append(text)
        self.master.update()                 # uebergibt den Inhalt an Windows

    def _kontextmenue_text(self, feld, mit_fehlern=False):
        tk = _tk

        def zeigen(ereignis):
            palette = THEMES[CURRENT_THEME]
            menue = tk.Menu(self.master, tearoff=0, bg=palette["CARD"], fg=palette["TEXT"],
                            activebackground=palette["ACCENT"],
                            activeforeground=palette["ON_ACCENT"], font=FONT_SMALL)
            try:
                auswahl = feld.get("sel.first", "sel.last")
            except tk.TclError:
                auswahl = ""
            menue.add_command(label=tr(_("Auswahl kopieren")),
                              state="normal" if auswahl else "disabled",
                              command=lambda: self.zwischenablage(auswahl))
            menue.add_command(label=tr(_("Alles kopieren")),
                              command=lambda: self.zwischenablage(feld.get("1.0", "end").rstrip()))
            if mit_fehlern:
                menue.add_command(label=tr(_("Fehlermeldungen kopieren")),
                                  state=str(self.knopf_fehler["state"]),
                                  command=self.fehler_kopieren)
                menue.add_separator()
                menue.add_command(label=tr(_("Leeren")), command=self.ausgabe_leeren)
            menue.tk_popup(ereignis.x_root, ereignis.y_root)
        feld.bind("<Button-3>", zeigen)

    # -- Zeitplan ------------------------------------------------------------------

    def zeitplan_anlegen(self, eintrag, sekunden):
        self.plan_nummer += 1
        plan_id = self.plan_nummer
        self.zeitplaene[plan_id] = {"eintrag": eintrag, "sekunden": sekunden, "auftrag": None}
        self._zeitplan_ausfuehren(plan_id)
        self.meldung(_("„{name}“ startet jetzt alle {sekunden} s.").format(
            name=eintrag["name"], sekunden=sekunden))

    def _zeitplan_ausfuehren(self, plan_id):
        plan = self.zeitplaene.get(plan_id)
        if not plan:
            return
        pfad = plan["eintrag"]["path"]
        if any(lauf["pfad"] == pfad for lauf in self.laeufe.values()):
            meldung = _("[Zeitplan] „{name}“ läuft noch – Termin übersprungen.").format(
                name=plan["eintrag"]["name"])
            text_schreiben(self.ausgabe, tr(meldung) + "\n", "warn")
        else:
            self.script_starten(plan["eintrag"])
        plan["auftrag"] = self.master.after(plan["sekunden"] * 1000,
                                            lambda: self._zeitplan_ausfuehren(plan_id))

    def zeitplan_beenden(self, plan_id):
        plan = self.zeitplaene.pop(plan_id, None)
        if plan and plan["auftrag"] is not None:
            self.master.after_cancel(plan["auftrag"])

    # -- Installationen ------------------------------------------------------------

    def installationen(self):
        return self.cfg["installationen"]

    def installation(self, schluessel):
        return next((i for i in self.installationen() if i["key"] == schluessel), None)

    def index(self, schluessel):
        """ModulIndex einer Installation - None, solange nichts eingelesen ist."""
        if schluessel not in self.indizes:
            daten = self.cfg["modul_daten"].get(schluessel)
            self.indizes[schluessel] = ModulIndex(daten) if daten and "dists" in daten else None
        return self.indizes[schluessel]

    def ausfuehrender_schluessel(self):
        gewaehlt = self.cfg.get("ausfuehren_mit")
        if self.installation(gewaehlt):
            return gewaehlt
        for marke in ("selbst", "doppelklick", "path"):
            for inst in self.installationen():
                if marke in inst.get("marken", ()):
                    return inst["key"]
        return self.installationen()[0]["key"] if self.installationen() else None

    def ausfuehrende_installation(self):
        return self.installation(self.ausfuehrender_schluessel())

    def _python_feld_fuellen(self):
        self._python_titel = [installation_titel(i) for i in self.installationen()]
        self.python_feld.configure(values=self._python_titel)
        inst = self.ausfuehrende_installation()
        self.python_feld.set(installation_titel(inst) if inst else tr(_("(noch nicht gesucht)")))

    def _python_gewaehlt(self, _ereignis=None):
        titel = self.python_feld.get()
        for inst in self.installationen():
            if installation_titel(inst) == titel:
                self.cfg["ausfuehren_mit"] = inst["key"]
                self.sichern()
                self.liste_zeichnen()
                for schluessel in self.modul_reiter_daten:
                    self._modul_baum_fuellen(schluessel)
                return

    def _beim_start_einlesen(self):
        """Beim ersten Start alles einlesen, sonst je nach Einstellung."""
        erststart = not self.installationen()
        if erststart or self.cfg["modul_aktualisierung"] == "auto":
            self.alles_einlesen()
        else:
            self._stand_anzeigen()

    def alles_einlesen(self):
        """Installationen suchen und die Module jeder Installation einlesen."""
        if self.einlesen_laeuft or self.pip_laeuft:
            return
        self._beschaeftigt(True, einlesen=True)
        self.status(_("Suche Python-Installationen …"), verlauf=True)
        weitere = list(self.cfg["weitere_interpreter"])

        def arbeit():
            try:
                gefunden = installationen_finden(weitere)
                self.im_hauptthread(self._installationen_uebernehmen, gefunden)
                for inst in gefunden:
                    self.im_hauptthread(self.status, _("Lese Module ein: {python} …").format(
                        python=installation_titel(inst)), True)
                    self.im_hauptthread(self._daten_uebernehmen, inst["key"],
                                        module_einlesen(inst["exe"]))
            except Exception as fehler:          # noqa: BLE001 - jede Panne melden
                self.im_hauptthread(self.meldung, _("Fehler beim Einlesen: {fehler}").format(
                    fehler=fehler), True)
            finally:
                self.im_hauptthread(self._einlesen_fertig)
        threading.Thread(target=arbeit, daemon=True).start()

    def installation_einlesen(self, schluessel):
        """Module einer einzelnen Installation neu einlesen."""
        inst = self.installation(schluessel)
        if not inst or self.einlesen_laeuft or self.pip_laeuft:
            return
        self._beschaeftigt(True, einlesen=True)
        self.status(_("Lese Module ein: {python} …").format(python=installation_titel(inst)),
                    verlauf=True)

        def arbeit():
            try:
                self.im_hauptthread(self._daten_uebernehmen, schluessel,
                                    module_einlesen(inst["exe"]))
            finally:
                self.im_hauptthread(self._einlesen_fertig)
        threading.Thread(target=arbeit, daemon=True).start()

    def _installationen_uebernehmen(self, gefunden):
        vorher = [i["key"] for i in self.installationen()]
        self.cfg["installationen"] = gefunden
        schluessel = {i["key"] for i in gefunden}
        for alt in list(self.cfg["modul_daten"]):
            if alt not in schluessel:
                del self.cfg["modul_daten"][alt]
        self.indizes.clear()
        if [i["key"] for i in gefunden] != vorher:
            self._modul_reiter_bauen()
        self._python_feld_fuellen()
        self.sichern()

    def _daten_uebernehmen(self, schluessel, daten):
        if "fehler" in daten:
            alt = self.cfg["modul_daten"].get(schluessel, {})
            alt["fehler"] = daten["fehler"]
            self.cfg["modul_daten"][schluessel] = alt
        else:
            self.cfg["modul_daten"][schluessel] = daten
            bekannt = self.cfg["bekannte_module"].setdefault(schluessel, {})
            for paket in daten["dists"]:
                bekannt[kanon(paket["name"])] = paket["name"]
        self.indizes.pop(schluessel, None)
        self._modul_baum_fuellen(schluessel)
        if schluessel == self.ausfuehrender_schluessel():
            self.liste_zeichnen()

    def _einlesen_fertig(self):
        self._beschaeftigt(False, einlesen=True)
        self.sichern()
        self._stand_anzeigen()
        self.liste_zeichnen()
        self._laufanzeige_auffrischen()

    def _stand_anzeigen(self):
        zeiten = [d.get("zeit") for d in self.cfg["modul_daten"].values() if d.get("zeit")]
        if zeiten:
            stand = datetime.fromisoformat(min(zeiten)).strftime("%d.%m.%Y %H:%M")
            self._stand = _("{anzahl} Installation(en) · Modullisten vom {zeit}").format(
                anzahl=len(self.installationen()), zeit=stand)
        else:
            self._stand = _("Modullisten noch nicht eingelesen")
        self.var_stand.set(self._stand)

    def installation_hinzufuegen(self):
        from tkinter import filedialog
        pfad = filedialog.askopenfilename(
            parent=self.master, title=tr(_("Python-Installation hinzufügen")),
            filetypes=[("python.exe", "python*.exe"), (tr(_("Alle Dateien")), "*.*")])
        if not pfad:
            return
        pfad = konsolen_python(os.path.normpath(pfad))
        if pfad not in self.cfg["weitere_interpreter"]:
            self.cfg["weitere_interpreter"].append(pfad)
        self.sichern()
        self.alles_einlesen()

    # -- Reiter 2: Module ----------------------------------------------------------

    def _seite_module_bauen(self, eltern) -> None:
        tk, ttk = _tk, _ttk
        raster = faerben(tk.Frame(eltern), bg="BG")
        raster.pack(fill="both", expand=True, padx=14, pady=14)

        # --- Werkzeuge ---
        oben = make_card(raster, fill="x")
        zeile = faerben(tk.Frame(oben), bg="CARD")
        zeile.pack(fill="x", padx=14, pady=(12, 6))
        self.modul_knoepfe = []
        for text, befehl, art, hinweis in (
                (_("Liste aktualisieren"), self.aktuelle_liste_aktualisieren, "primary",
                 _("Liest die Module der gewählten Installation neu ein: neu installierte "
                   "kommen hinzu, entfernte werden als fehlend markiert.")),
                (_("Alle Installationen neu einlesen"), self.alles_einlesen, "secondary",
                 _("Sucht erneut nach Python-Installationen und liest ihre Module ein.")),
                (_("Konsole öffnen"), self.konsole_oeffnen, "secondary",
                 _("Öffnet eine Eingabeaufforderung, in der python und pip zur gewählten "
                   "Installation gehören.")),
                (_("Ordner öffnen"), self.ordner_oeffnen, "secondary",
                 _("Öffnet den Ordner der gewählten Installation im Explorer, "
                   "python.exe ist dort markiert.")),
                (_("Installation hinzufügen …"), self.installation_hinzufuegen, "secondary",
                 _("Eine Installation oder virtuelle Umgebung von Hand aufnehmen, die die "
                   "Suche nicht findet."))):
            knopf = FlatButton(zeile, text, befehl, kind=art, tooltip=hinweis)
            knopf.pack(side="left", padx=(0, 8))
            self.modul_knoepfe.append(knopf)

        # Die Einstellung steht in der Suchzeile: In der Schalterzeile wuerde
        # sie bei schmalem Fenster von den Schaltern zusammengedrueckt.
        suche = faerben(tk.Frame(oben), bg="CARD")
        suche.pack(fill="x", padx=14, pady=(0, 12))
        rechts = faerben(tk.Frame(suche), bg="CARD")
        rechts.pack(side="right", padx=(16, 0))
        beschriften(faerben(tk.Label(rechts, font=FONT_SMALL), bg="CARD", fg="MUTED"),
                    _("Modullisten aktualisieren")).pack(side="left", padx=(0, 8))
        self.modus_feld = ttk.Combobox(rechts, state="readonly", font=FONT_SMALL, width=16)
        self.modus_feld.pack(side="left")
        self.modus_feld.bind("<<ComboboxSelected>>", self._modus_gewaehlt)
        Tooltip(self.modus_feld, _("Automatisch: bei jedem Programmstart und nach dem Schließen "
                                   "der Konsole.\nDurch Benutzer: nur beim ersten Start und "
                                   "auf Knopfdruck."))
        self._modus_feld_fuellen()

        beschriften(faerben(tk.Label(suche, font=FONT_SMALL), bg="CARD", fg="MUTED"),
                    _("Suche")).pack(side="left", padx=(0, 8))
        ttk.Entry(suche, textvariable=self.var_suche, font=FONT_SMALL).pack(
            side="left", fill="x", expand=True)

        # --- pip-Protokoll (unten) ---
        protokoll = make_card(raster, side="bottom", fill="x", pady=(12, 0))
        kopf = faerben(tk.Frame(protokoll), bg="CARD")
        kopf.pack(fill="x", padx=14, pady=(10, 6))
        card_title(kopf, _("pip-Protokoll"), side="left")
        FlatButton(kopf, _("Kopieren"),
                   lambda: self.zwischenablage(self.pip_text.get("1.0", "end").rstrip())
                   ).pack(side="right")
        FlatButton(kopf, _("Leeren"), lambda: text_leeren(self.pip_text)).pack(
            side="right", padx=(0, 8))
        rahmen, self.pip_text = textfeld(protokoll, hoehe=4)
        rahmen.pack(fill="x", padx=14, pady=(0, 12))
        text_tags_faerben(self.pip_text)
        self._kontextmenue_text(self.pip_text)

        # --- Aktionen ---
        aktionen = faerben(tk.Frame(raster), bg="BG")
        aktionen.pack(side="bottom", fill="x", pady=(10, 0))
        for text, befehl, art in (
                (_("Installieren …"), self._auswahl_installieren, "primary"),
                (_("Deinstallieren …"), self._auswahl_deinstallieren, "danger"),
                (_("Aktualisieren (Upgrade)"), self._auswahl_upgrade, "secondary"),
                (_("Info"), self._auswahl_info, "secondary"),
                (_("Modul hinzufügen …"), self._modul_hinzufuegen, "secondary")):
            knopf = FlatButton(aktionen, text, befehl, kind=art)
            knopf.pack(side="left", padx=(0, 8))
            self.modul_knoepfe.append(knopf)
        beschriften(faerben(tk.Label(aktionen, font=FONT_TINY, anchor="e"), bg="BG", fg="MUTED"),
                    _("Rechtsklick auf ein Modul öffnet alle Aktionen.")).pack(side="right")

        # --- Reiter je Installation ---
        self.modul_reiter = ttk.Notebook(raster, style="Innen.TNotebook")
        self.modul_reiter.pack(fill="both", expand=True, pady=(12, 0))
        self.modul_reiter.bind("<<NotebookTabChanged>>", self._modul_reiter_gewechselt)
        self._modul_reiter_bauen()

    def _modus_feld_fuellen(self):
        self._modi = [("auto", _("automatisch")), ("manuell", _("durch Benutzer"))]
        self.modus_feld.configure(values=[tr(t) for _m, t in self._modi])
        self.modus_feld.set(tr(dict(self._modi)[self.cfg["modul_aktualisierung"]]))

    def _modus_gewaehlt(self, _ereignis=None):
        for modus, text in self._modi:
            if tr(text) == self.modus_feld.get():
                self.cfg["modul_aktualisierung"] = modus
                self.sichern()

    def _modul_reiter_bauen(self):
        tk, ttk = _tk, _ttk
        for daten in self.modul_reiter_daten.values():
            daten["seite"].destroy()
        self.modul_reiter_daten = {}
        if not self.installationen():
            seite = faerben(tk.Frame(self.modul_reiter), bg="CARD")
            self.modul_reiter.add(seite, text="  …  ")
            beschriften(faerben(tk.Label(seite, font=FONT_SMALL), bg="CARD", fg="MUTED"),
                        _("Die Python-Installationen werden gesucht …")).pack(pady=30)
            self.modul_reiter_daten[""] = {"seite": seite, "baum": None, "info": None}
            return
        for inst in self.installationen():
            seite = faerben(tk.Frame(self.modul_reiter), bg="CARD")
            self.modul_reiter.add(seite, text=f"  {installation_titel(inst)}  ")
            info = faerben(tk.Label(seite, font=FONT_TINY, anchor="w", justify="left"),
                           bg="CARD", fg="MUTED")
            info.pack(fill="x", padx=10, pady=(8, 6))
            rahmen = faerben(tk.Frame(seite), bg="CARD")
            rahmen.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            baum = ttk.Treeview(rahmen, columns=("version", "status", "importe", "benoetigt"),
                                selectmode="browse")
            s = self.skalierung
            for spalte, titel, breite, strecken in (
                    ("#0", _("Paket"), 230, True), ("version", _("Version"), 90, False),
                    ("status", _("Status"), 90, False), ("importe", _("Importnamen"), 200, True),
                    ("benoetigt", _("Benötigt von"), 240, True)):
                baum.column(spalte, width=round(breite * s), minwidth=round(60 * s),
                            stretch=strecken)
                beschriftung_merken(lambda neu, b=baum, sp=spalte: b.heading(sp, text=neu), titel)
            rollen = ttk.Scrollbar(rahmen, orient="vertical", command=baum.yview)
            baum.configure(yscrollcommand=rollen.set)
            rollen.pack(side="right", fill="y")
            baum.pack(side="left", fill="both", expand=True)
            baum.bind("<<TreeviewOpen>>", lambda _e, k=inst["key"]: self._zweig_oeffnen(k))
            baum.bind("<Button-3>", lambda e, k=inst["key"]: self._modul_kontextmenue(k, e))
            baum.bind("<Double-Button-1>", lambda _e: self._auswahl_info())
            baum.bind("<Delete>", lambda _e: self._auswahl_deinstallieren())
            self.modul_reiter_daten[inst["key"]] = {"seite": seite, "baum": baum, "info": info}
            self._baum_tags(baum)
            self._modul_baum_fuellen(inst["key"])
        gemerkt = self.cfg.get("modul_reiter")
        if gemerkt in self.modul_reiter_daten:
            self.modul_reiter.select(self.modul_reiter_daten[gemerkt]["seite"])

    def _baum_tags(self, baum):
        palette = THEMES[CURRENT_THEME]
        baum.tag_configure("fehlt", foreground=palette["DANGER"])
        baum.tag_configure("kind", foreground=palette["MUTED"])
        baum.tag_configure("kind_fehlt", foreground=palette["DANGER"])
        baum.tag_configure("hinweis", foreground=palette["MUTED"])

    def _modul_reiter_gewechselt(self, _ereignis=None):
        schluessel = self.aktiver_modul_schluessel()
        if schluessel:
            self.cfg["modul_reiter"] = schluessel

    def aktiver_modul_schluessel(self):
        try:
            aktuell = self.modul_reiter.select()
        except _tk.TclError:
            return None
        for schluessel, daten in self.modul_reiter_daten.items():
            if str(daten["seite"]) == str(aktuell):
                return schluessel or None
        return None

    def _info_zeile(self, schluessel):
        inst = self.installation(schluessel)
        daten = self.cfg["modul_daten"].get(schluessel, {})
        teile = [inst["exe"]]
        marken = [tr(_(MARKEN[m])) for m in inst.get("marken", ()) if m in MARKEN]
        if marken:
            teile.append(" · ".join(marken))
        if daten.get("zeit"):
            teile.append(tr(_("Stand: {zeit}").format(zeit=datetime.fromisoformat(
                daten["zeit"]).strftime("%d.%m.%Y %H:%M"))))
        if "dists" in daten:
            teile.append(tr(_("{anzahl} Pakete").format(anzahl=len(daten["dists"]))))
            if not daten.get("pip"):
                teile.append(tr(_("pip fehlt")))
        if daten.get("fehler"):
            teile.append(tr(_("Fehler beim Einlesen: {fehler}").format(
                fehler=daten["fehler"].splitlines()[-1][:160])))
        return "   ·   ".join(teile)

    def _modul_baum_fuellen(self, schluessel):
        """Liste einer Installation: installierte, fehlende und gewuenschte Module."""
        reiter = self.modul_reiter_daten.get(schluessel)
        if not reiter or reiter["baum"] is None:
            return
        baum = reiter["baum"]
        reiter["info"].configure(text=self._info_zeile(schluessel))
        offen = {i for i in baum.get_children() if baum.item(i, "open")}
        auswahl = baum.selection()
        baum.delete(*baum.get_children())
        index = self.index(schluessel)
        if index is None:
            baum.insert("", "end", iid="__hinweis", tags=("hinweis",),
                        text=tr(_("Noch nicht eingelesen – „Liste aktualisieren“ liest die "
                                  "Module ein.")))
            return

        zeilen = {}
        for kname, paket in index.pakete.items():
            zeilen[kname] = {"name": paket["name"], "version": paket["version"], "fehlt": False,
                             "scripts": []}
        for kname, anzeige in self.cfg["bekannte_module"].get(schluessel, {}).items():
            zeilen.setdefault(kname, {"name": anzeige, "version": "", "fehlt": True,
                                      "scripts": []})
        if schluessel == self.ausfuehrender_schluessel():
            for name, scripts in self.fehlende_fuer_scripts().items():
                zeile = zeilen.setdefault(kanon(name), {"name": name, "version": "",
                                                        "fehlt": True, "scripts": []})
                zeile["scripts"] += scripts

        weitere = [self.index(i["key"]) for i in self.installationen() if i["key"] != schluessel]
        suche = self.var_suche.get().strip().lower()
        for kname in sorted(zeilen):
            zeile = zeilen[kname]
            if zeile["fehlt"]:
                importe = next((", ".join(w.pakete[kname].get("top", ())) for w in weitere
                                if w and kname in w.pakete), "")
            else:
                importe = ", ".join(t for t in index.pakete[kname].get("top", ())
                                    if not t.startswith("_")) or ", ".join(
                    index.pakete[kname].get("top", ()))
            if suche and suche not in kname and suche not in zeile["name"].lower() \
                    and suche not in importe.lower():
                continue
            benoetigt = sorted(index.rueck.get(kname, []), key=str.lower)
            benoetigt += [tr(_("Script „{name}“").format(name=n)) for n in zeile["scripts"]]
            baum.insert("", "end", iid=kname, text=zeile["name"],
                        values=(zeile["version"] or "–",
                                tr(_("fehlt")) if zeile["fehlt"] else tr(_("installiert")),
                                importe, ", ".join(benoetigt)),
                        tags=("fehlt",) if zeile["fehlt"] else ())
            if not zeile["fehlt"] and index.pakete[kname].get("requires"):
                baum.insert(kname, "end", iid=kname + "/__platzhalter", text="…")
                if kname in offen:
                    baum.item(kname, open=True)
                    self._zweig_fuellen(schluessel, kname)
        if auswahl and baum.exists(auswahl[0]):
            baum.selection_set(auswahl[0])
            baum.see(auswahl[0])

    def _zweig_oeffnen(self, schluessel):
        baum = self.modul_reiter_daten[schluessel]["baum"]
        self._zweig_fuellen(schluessel, baum.focus())

    def _zweig_fuellen(self, schluessel, iid):
        """Abhaengigkeiten eines Pakets erst beim Aufklappen einfuegen.

        Jede Ebene zeigt, was das Paket braucht - und ob es vorhanden ist.
        Der Pfad im iid verhindert Endlosschleifen bei gegenseitigen
        Abhaengigkeiten.
        """
        baum = self.modul_reiter_daten[schluessel]["baum"]
        platzhalter = iid + "/__platzhalter"
        if not iid or not baum.exists(platzhalter):
            return
        baum.delete(platzhalter)
        index = self.index(schluessel)
        paket = index.pakete.get(iid.split("/")[-1]) if index else None
        if not paket:
            return
        vorfahren = set(iid.split("/"))
        for anforderung in paket.get("requires", ()):
            kname = kanon(anforderung)
            kind = f"{iid}/{kname}"
            unterpaket = index.pakete.get(kname)
            baum.insert(iid, "end", iid=kind, text=unterpaket["name"] if unterpaket
                        else anforderung,
                        values=(unterpaket["version"] if unterpaket else "–",
                                tr(_("installiert")) if unterpaket else tr(_("fehlt")),
                                ", ".join(unterpaket.get("top", ())) if unterpaket else "", ""),
                        tags=("kind",) if unterpaket else ("kind_fehlt",))
            if unterpaket and unterpaket.get("requires") and kname not in vorfahren:
                baum.insert(kind, "end", iid=kind + "/__platzhalter", text="…")

    def _suche_geaendert(self):
        for schluessel in self.modul_reiter_daten:
            if schluessel:
                self._modul_baum_fuellen(schluessel)

    def _gewaehltes_modul(self):
        """(Schluessel, Paketname) des markierten Moduls oder None."""
        schluessel = self.aktiver_modul_schluessel()
        if not schluessel:
            return None
        baum = self.modul_reiter_daten[schluessel]["baum"]
        auswahl = baum.selection()
        if not auswahl or auswahl[0].startswith("__") or auswahl[0].endswith("__platzhalter"):
            return None
        return schluessel, baum.item(auswahl[0], "text")

    def _auswahl_oder_hinweis(self):
        gewaehlt = self._gewaehltes_modul()
        if not gewaehlt:
            melden(self, _("Module"), _("Bitte zuerst ein Modul in der Liste auswählen."))
        return gewaehlt

    def _auswahl_installieren(self):
        gewaehlt = self._auswahl_oder_hinweis()
        if gewaehlt:
            self.installieren_anfragen([gewaehlt[1]], gewaehlt[0])

    def _auswahl_deinstallieren(self):
        gewaehlt = self._auswahl_oder_hinweis()
        if gewaehlt:
            self.deinstallieren_anfragen(gewaehlt[1], gewaehlt[0])

    def _auswahl_upgrade(self):
        gewaehlt = self._auswahl_oder_hinweis()
        if gewaehlt:
            self.installieren_anfragen([gewaehlt[1]], gewaehlt[0], upgrade=True)

    def _auswahl_info(self):
        gewaehlt = self._auswahl_oder_hinweis()
        if gewaehlt:
            ModulInfoFenster(self, gewaehlt[0], gewaehlt[1])

    def _modul_hinzufuegen(self):
        schluessel = self.aktiver_modul_schluessel()
        if not schluessel:
            return
        dialog = Dialog(self, _("Modul hinzufügen"),
                        _("Name des Pakets, wie er bei pip install angegeben wird:"),
                        [(_("Abbrechen"), None, "secondary"), (_("Weiter"), True, "primary")],
                        eingabe="")
        if dialog.ergebnis and dialog.eingabe_text:
            self.installieren_anfragen(dialog.eingabe_text.split(), schluessel)

    def _modul_kontextmenue(self, schluessel, ereignis):
        tk = _tk
        baum = self.modul_reiter_daten[schluessel]["baum"]
        iid = baum.identify_row(ereignis.y)
        if not iid or iid.startswith("__") or iid.endswith("__platzhalter"):
            return
        baum.selection_set(iid)
        baum.focus(iid)
        name = baum.item(iid, "text")
        index = self.index(schluessel)
        installiert = bool(index and index.ist_installiert(name))
        bekannt = self.cfg["bekannte_module"].get(schluessel, {})
        palette = THEMES[CURRENT_THEME]
        menue = tk.Menu(self.master, tearoff=0, bg=palette["CARD"], fg=palette["TEXT"],
                        activebackground=palette["ACCENT"], activeforeground=palette["ON_ACCENT"],
                        disabledforeground=palette["BTN_DISABLED"], font=FONT_SMALL)
        frei = "disabled" if (self.pip_laeuft or self.einlesen_laeuft) else "normal"
        menue.add_command(label=tr(_("Installieren …")),
                          state=frei if not installiert else "disabled",
                          command=lambda: self.installieren_anfragen([name], schluessel))
        menue.add_command(label=tr(_("Deinstallieren …")),
                          state=frei if installiert else "disabled",
                          command=lambda: self.deinstallieren_anfragen(name, schluessel))
        menue.add_command(label=tr(_("Aktualisieren (Upgrade)")),
                          state=frei if installiert else "disabled",
                          command=lambda: self.installieren_anfragen([name], schluessel,
                                                                     upgrade=True))
        menue.add_separator()
        menue.add_command(label=tr(_("Info")),
                          command=lambda: ModulInfoFenster(self, schluessel, name))
        menue.add_command(label=tr(_("Namen kopieren")), command=lambda: self.zwischenablage(name))
        if not installiert and "/" not in iid and kanon(name) in bekannt:
            menue.add_separator()
            menue.add_command(label=tr(_("Aus der Liste entfernen")),
                              command=lambda: self._vergessen(schluessel, name))
        menue.tk_popup(ereignis.x_root, ereignis.y_root)

    def _vergessen(self, schluessel, name):
        self.cfg["bekannte_module"].get(schluessel, {}).pop(kanon(name), None)
        self.sichern()
        self._modul_baum_fuellen(schluessel)

    def aktuelle_liste_aktualisieren(self):
        schluessel = self.aktiver_modul_schluessel()
        if schluessel:
            self.installation_einlesen(schluessel)
        else:
            self.alles_einlesen()

    def ordner_oeffnen(self):
        """Explorer im Ordner der gewaehlten Installation, python.exe markiert."""
        inst = self.installation(self.aktiver_modul_schluessel())
        if not inst:
            return
        if not os.path.isfile(inst["exe"]):
            melden(self, _("Ordner öffnen"), _("Der Ordner wurde nicht gefunden: {pfad}").format(
                pfad=os.path.dirname(inst["exe"])), art="fehler")
            return
        try:
            # explorer.exe meldet auch bei Erfolg oft Exit-Code 1 - daher kein run()
            subprocess.Popen(["explorer.exe", "/select,", os.path.normpath(inst["exe"])])
        except OSError as fehler:
            melden(self, _("Ordner öffnen"), str(fehler), art="fehler")
            return
        self.meldung(_("Ordner von {python} geöffnet.").format(python=installation_titel(inst)))

    def konsole_oeffnen(self):
        """Eingabeaufforderung, in der python und pip zur gewaehlten Installation gehoeren."""
        inst = self.installation(self.aktiver_modul_schluessel())
        if not inst:
            return
        ordner = os.path.dirname(inst["exe"])
        umgebung = os.environ.copy()
        pfade = [ordner, os.path.join(ordner, "Scripts")]
        umgebung["PATH"] = os.pathsep.join(pfade + [umgebung.get("PATH", "")])
        titel = installation_titel(inst)
        hinweis = tr(_("Hier gehören python und pip zu {python}. Beispiel: pip install "
                       "paketname").format(python=titel))
        befehl = (f"chcp 65001 >nul & title {titel} & echo {hinweis} & echo."
                  " & python -m pip --version")
        try:
            prozess = subprocess.Popen(["cmd.exe", "/k", befehl], cwd=os.path.expanduser("~"),
                                       env=umgebung, creationflags=NEUE_KONSOLE)
        except OSError as fehler:
            melden(self, _("Konsole öffnen"), str(fehler), art="fehler")
            return
        self.meldung(_("Konsole für {python} geöffnet.").format(python=titel))
        if self.cfg["modul_aktualisierung"] == "auto":
            schluessel = inst["key"]

            def warten():
                prozess.wait()
                self.im_hauptthread(self._nach_konsole, schluessel)
            threading.Thread(target=warten, daemon=True).start()

    def _nach_konsole(self, schluessel):
        if self.einlesen_laeuft or self.pip_laeuft:
            return
        self.installation_einlesen(schluessel)

    # -- Installieren und Deinstallieren -------------------------------------------

    def _beschaeftigt(self, an, einlesen=False, pip=False):
        if einlesen:
            self.einlesen_laeuft = an
        if pip:
            self.pip_laeuft = an
        frei = not (self.einlesen_laeuft or self.pip_laeuft)
        for knopf in self.modul_knoepfe:
            knopf.configure(state="normal" if frei else "disabled")
        self.master.configure(cursor="" if frei else "watch")

    def _besetzt(self):
        if self.pip_laeuft or self.einlesen_laeuft:
            melden(self, _("Module"), _("Bitte warten, bis der laufende Vorgang fertig ist."))
            return True
        return False

    def installieren_anfragen(self, namen, schluessel, upgrade=False):
        """Rueckfrage zum Installieren - in eine oder in alle Installationen."""
        if self._besetzt():
            return
        inst = self.installation(schluessel)
        if not inst:
            return
        liste = ", ".join(namen)
        optionen = [(tr(_("Nur in {python}").format(python=installation_titel(inst))), "eine")]
        andere = [i for i in self.installationen() if i["key"] != schluessel]
        if andere:
            optionen.append((tr(_("In allen kompatiblen Installationen ({anzahl})").format(
                anzahl=len(andere) + 1)), "alle"))
        titel = _("Modul aktualisieren") if upgrade else _("Modul installieren")
        frage = (_("„{namen}“ auf die neueste Version aktualisieren?") if upgrade
                 else _("„{namen}“ installieren?")).format(namen=liste)
        hinweis = None
        index = self.index(schluessel)
        if index is not None and not index.pip:
            hinweis = _("In dieser Installation fehlt pip. Es lässt sich in der Konsole mit "
                        "„python -m ensurepip“ nachrüsten.")
        dialog = Dialog(self, titel, frage,
                        [(_("Abbrechen"), None, "secondary"),
                         (_("Aktualisieren") if upgrade else _("Installieren"), True, "primary")],
                        optionen=optionen if len(optionen) > 1 else None, hinweis=hinweis)
        if not dialog.ergebnis:
            return
        ziele = [inst] if dialog.option != "alle" else [inst] + andere
        auftraege = []
        for ziel in ziele:
            ziel_index = self.index(ziel["key"])
            offen = namen if upgrade or ziel_index is None else [
                n for n in namen if not ziel_index.ist_installiert(n)]
            if not offen:
                continue
            argumente = ["install"] + (["--upgrade"] if upgrade else []) + list(offen)
            auftraege.append((ziel, argumente, f"pip {' '.join(argumente)}"))
        if not auftraege:
            melden(self, titel, _("Überall schon vorhanden – nichts zu tun."))
            return
        for name in namen:                    # soll auch nach einem Fehlschlag in der Liste stehen
            self.cfg["bekannte_module"].setdefault(schluessel, {}).setdefault(kanon(name), name)
        self.pip_ausfuehren(auftraege)

    def deinstallieren_anfragen(self, name, schluessel):
        """Sicherheitsabfrage vor jeder Deinstallation - egal, woher sie kommt."""
        if self._besetzt():
            return
        vorhanden = [i for i in self.installationen()
                     if self.index(i["key"]) and self.index(i["key"]).ist_installiert(name)]
        if not vorhanden:
            melden(self, _("Modul deinstallieren"),
                   _("„{name}“ ist in keiner Installation vorhanden.").format(name=name))
            return
        inst = self.installation(schluessel)
        optionen = []
        if inst in vorhanden:
            optionen.append((tr(_("Nur aus {python}").format(
                python=installation_titel(inst))), "eine"))
        if len(vorhanden) > 1 or inst not in vorhanden:
            optionen.append((tr(_("Aus allen Installationen, die es enthalten ({anzahl})")
                                .format(anzahl=len(vorhanden))), "alle"))
        warnungen = []
        for ziel in vorhanden:
            brauchen = self.index(ziel["key"]).rueck.get(kanon(name), [])
            if brauchen:
                warnungen.append(tr(_("{python}: wird noch gebraucht von {pakete}").format(
                    python=installation_titel(ziel), pakete=", ".join(sorted(brauchen)))))
        scripts = self.scripts_mit_paket(name)
        if scripts:
            warnungen.append(tr(_("Diese Scripts verwenden es: {scripts}").format(
                scripts=", ".join(scripts))))
        if kanon(name) in ("pip", "setuptools", "wheel"):
            warnungen.append(tr(_("Achtung: {name} gehört zur Grundausstattung von Python. "
                                  "Ohne pip lassen sich keine Module mehr installieren.").format(
                name=name)))
        dialog = Dialog(self, _("Modul deinstallieren"),
                        _("„{name}“ wirklich deinstallieren? Das Modul bleibt als fehlend in "
                          "der Liste und lässt sich von dort wieder installieren.").format(
                            name=name),
                        [(_("Abbrechen"), None, "secondary"),
                         (_("Deinstallieren"), True, "danger")],
                        optionen=optionen if len(optionen) > 1 else None,
                        vorwahl=optionen[0][1], hinweis="\n".join(warnungen) or None,
                        hinweis_rolle="DANGER")
        if not dialog.ergebnis:
            return
        ziele = vorhanden if dialog.option == "alle" or inst not in vorhanden else [inst]
        self.pip_ausfuehren([(ziel, ["uninstall", "-y", name], f"pip uninstall {name}")
                             for ziel in ziele])

    def pip_ausfuehren(self, auftraege):
        """pip-Auftraege nacheinander abarbeiten und die Listen danach auffrischen."""
        self._beschaeftigt(True, pip=True)
        self.reiter.select(1)
        self.status(_("pip arbeitet …"), verlauf=True)

        def arbeit():
            ergebnisse = []
            for inst, argumente, beschreibung in auftraege:
                titel = installation_titel(inst)
                self.im_hauptthread(self._pip_protokoll,
                                    f"\n▶ {beschreibung}   [{titel}]\n", "info")
                befehl = [inst["exe"], "-m", "pip", *argumente, "--disable-pip-version-check",
                          "--no-input"]
                try:
                    prozess = subprocess.Popen(
                        befehl, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                        encoding="utf-8", errors="replace", bufsize=1, env=utf8_umgebung(),
                        stdin=subprocess.DEVNULL, cwd=tempfile.gettempdir(),
                        creationflags=OHNE_FENSTER)
                    for zeile in iter(prozess.stdout.readline, ""):
                        art = "fehler" if re.match(r"\s*(ERROR|FEHLER)", zeile) else None
                        self.im_hauptthread(self._pip_protokoll, zeile, art)
                    code = prozess.wait()
                except OSError as fehler:
                    self.im_hauptthread(self._pip_protokoll, f"{fehler}\n", "fehler")
                    code = -1
                ergebnisse.append((inst, beschreibung, code))
            betroffen = {inst["key"]: inst for inst, _b, _c in ergebnisse}
            for schluessel, inst in betroffen.items():
                self.im_hauptthread(self.status, _("Lese Module ein: {python} …").format(
                    python=installation_titel(inst)), True)
                self.im_hauptthread(self._daten_uebernehmen, schluessel,
                                    module_einlesen(inst["exe"]))
            self.im_hauptthread(self._pip_fertig, ergebnisse)
        threading.Thread(target=arbeit, daemon=True).start()

    def _pip_protokoll(self, text, art=None):
        text_schreiben(self.pip_text, text, art)

    def _pip_fertig(self, ergebnisse):
        self._beschaeftigt(False, pip=True)
        fehlgeschlagen = [(inst, b) for inst, b, code in ergebnisse if code != 0]
        for inst, beschreibung, code in ergebnisse:
            text = (_("✓ Erfolgreich: {befehl} [{python}]") if code == 0 else
                    _("✗ Fehlgeschlagen (nicht kompatibel oder nicht erreichbar): {befehl} "
                      "[{python}]")).format(befehl=beschreibung, python=installation_titel(inst))
            self._pip_protokoll(tr(text) + "\n", "ok" if code == 0 else "fehler")
        self.sichern()
        self._stand_anzeigen()
        self.liste_zeichnen()
        self._laufanzeige_auffrischen()      # Zustand zuruecksetzen, bevor die Meldung kommt
        if fehlgeschlagen:
            self.meldung(_("pip meldet Fehler – Einzelheiten im pip-Protokoll."), fehler=True)
        else:
            self.meldung(_("pip ist fertig."))

    # -- Reiter 3: Info ---------------------------------------------------------

    def _seite_info_bauen(self, eltern) -> None:
        tk = _tk
        raster = faerben(tk.Frame(eltern), bg="BG")
        raster.pack(fill="both", expand=True, padx=14, pady=14)

        karte = make_card(raster, fill="x")
        card_title(karte, f"{PROGRAMM} {VERSION}")
        card_text(karte, _("Startet Python-Scripts mit sichtbarer Ausgabe, prüft vorab ihre "
                           "Abhängigkeiten und verwaltet die Module jeder gefundenen "
                           "Python-Installation."))
        card_text(karte, "Copyright 2026 Alexander Unverhau", rolle="TEXT")
        card_text(karte, _("Erstellt mit Unterstützung von Claude AI"))
        card_text(karte, _("Veröffentlicht unter der MIT-Lizenz."))

        karte_technik = make_card(raster, fill="x", pady=(12, 0))
        card_title(karte_technik, _("Technisches"))
        gitter = faerben(tk.Frame(karte_technik), bg="CARD")
        gitter.pack(fill="x", padx=14, pady=(0, 12))
        gitter.columnconfigure(1, weight=1)
        zeilen = (
            (_("Python"), sys.version.split()[0]),
            (_("Tkinter"), f"Tk {tk.TkVersion}"),
            (_("Einstellungen"), config_path()),
        )
        for reihe, (name, wert) in enumerate(zeilen):
            beschriften(faerben(tk.Label(gitter, font=FONT_SMALL, anchor="w"),
                                bg="CARD", fg="MUTED"), name).grid(row=reihe, column=0,
                                                                   sticky="w", pady=1)
            # wraplength deckelt die Breite: Der Ablageort ist ein Dateipfad
            # und kann beliebig lang sein.
            faerben(tk.Label(gitter, text=wert, font=FONT_MONO_SMALL, anchor="w",
                             justify="left", wraplength=620),
                    bg="CARD", fg="TEXT").grid(row=reihe, column=1, sticky="w", padx=(12, 0))

    # -- Status ------------------------------------------------------------------

    # Die Statusleiste kennt zwei Arten von Text:
    # - status(): der Zustand ("Bereit.", "pip arbeitet …"). Er bleibt stehen,
    #   bis sich der Zustand aendert.
    # - meldung(): die Rueckmeldung auf eine Aktion. Sie traegt Uhrzeit und den
    #   Vorsatz "Letzte Aktion" und weicht nach MELDUNG_MS wieder dem Zustand -
    #   sonst stuende etwa "Konsole für Python X geöffnet" noch da, wenn man
    #   laengst mit Python Y arbeitet.

    MELDUNG_MS = 8000
    FEHLER_MS = 30000

    def status(self, text, verlauf=False) -> None:
        """Zustand setzen. verlauf=True verdraengt eine noch sichtbare Meldung."""
        self._status = text
        if verlauf or self._meldung is None:
            self._meldung_beenden()
            self.var_status.set(tr(text))

    def meldung(self, text, fehler=False) -> None:
        """Rueckmeldung zeigen, die sich nach kurzer Zeit selbst ausblendet."""
        self._meldung_beenden()
        self._meldung = _("Letzte Aktion ({zeit}): {text}").format(
            zeit=datetime.now().strftime("%H:%M:%S"), text=text)
        self.var_status.set(tr(self._meldung))
        self._meldung_auftrag = self.master.after(
            self.FEHLER_MS if fehler else self.MELDUNG_MS, self._meldung_ablaufen)

    def _meldung_ablaufen(self) -> None:
        self._meldung_auftrag = None
        self._meldung = None
        if self._status is not None:
            self.var_status.set(tr(self._status))

    def _meldung_beenden(self) -> None:
        if self._meldung_auftrag is not None:
            self.master.after_cancel(self._meldung_auftrag)
        self._meldung_auftrag = None
        self._meldung = None

    def _laufende_texte_auffrischen(self) -> None:
        if self._meldung is not None:
            self.var_status.set(tr(self._meldung))
        elif self._status is not None:
            self.var_status.set(tr(self._status))
        if getattr(self, "_stand", None) is not None:
            self.var_stand.set(tr(self._stand))

    # -- Sprache und Farbschema ---------------------------------------------------

    def _sprache_gewaehlt(self, _ereignis=None) -> None:
        gewaehlt = self.sprachfeld.get()
        for code, name in self.sprachnamen.items():
            if name == gewaehlt:
                self.sprache_setzen(code)
                return

    def sprache_setzen(self, code: str) -> None:
        if code == _.language:
            return
        _.language = code
        self.sichern()
        fortsetzen = zeichnen_anhalten(self.master.winfo_id())
        try:
            texte_auffrischen()
            self._laufende_texte_auffrischen()
            self.sprachfeld.set(self.sprachnamen.get(code, self.sprachfeld.get()))
            self._modus_feld_fuellen()
            self._python_feld_fuellen()
            self.liste_zeichnen()
            for schluessel in self.modul_reiter_daten:
                self._modul_baum_fuellen(schluessel)
            self.master.update_idletasks()
        finally:
            fortsetzen()

    def _schema_umgeschaltet(self) -> None:
        self.schema_setzen("dark" if self.var_dunkel.get() else "light")

    def schema_setzen(self, name: str) -> None:
        if name == CURRENT_THEME:
            return
        apply_theme(name)
        self.sichern()
        fortsetzen = zeichnen_anhalten(self.master.winfo_id())
        try:
            self.master.configure(bg=BG)
            self._stil_setzen()
            farben_auffrischen()
            for feld in (self.ausgabe, self.pip_text):
                text_tags_faerben(feld)
            for daten in self.modul_reiter_daten.values():
                if daten["baum"] is not None:
                    self._baum_tags(daten["baum"])
            self.liste_zeichnen()
            self.master.update_idletasks()
        finally:
            fortsetzen()

    # -- Schliessen ----------------------------------------------------------------

    def schliessen(self) -> None:
        if self.laeufe:
            dialog = Dialog(self, _("Programm beenden"),
                            _("Es laufen noch {anzahl} Script(s). Beim Schließen werden sie "
                              "beendet.").format(anzahl=len(self.laeufe)),
                            [(_("Abbrechen"), None, "secondary"),
                             (_("Scripts beenden und schließen"), True, "danger")])
            if not dialog.ergebnis:
                return
            for lauf in list(self.laeufe.values()):
                try:
                    lauf["prozess"].kill()
                except OSError:
                    pass
        for plan_id in list(self.zeitplaene):
            self.zeitplan_beenden(plan_id)
        if self._fenster_auftrag is not None:
            self.master.after_cancel(self._fenster_auftrag)
        self._meldung_beenden()
        if self._bereit:
            self._fensterlage_sichern()
        self.sichern()
        self.master.destroy()


# --------------------------------------------------------------------------
# Start
# --------------------------------------------------------------------------

def dpi_bewusstsein_aktivieren() -> float:
    """Meldet die Anwendung unter Windows als DPI-bewusst an.

    Ohne diese Anmeldung vergroessert Windows das Fenster nur als Bitmap - die
    Schrift wirkt dann unscharf. Rueckgabe ist die Systemskalierung.
    """
    if sys.platform != "win32":
        return 1.0
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)      # System-DPI beachten
        return ctypes.windll.user32.GetDpiForSystem() / 96.0
    except (AttributeError, OSError):                        # aeltere Windows-Fassungen
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError, NameError):
            pass
        return 1.0


def startfehler_melden(text: str) -> None:
    """Startfehler auf der Konsole und - wenn moeglich - in einem Fenster zeigen."""
    if sys.stderr is not None:
        print(text, file=sys.stderr)
    try:
        import tkinter as tk
        from tkinter import messagebox
        wurzel = tk.Tk()
        wurzel.withdraw()
        messagebox.showerror(f"{PROGRAMM} {VERSION}", text)
        wurzel.destroy()
    except Exception:                       # ohne Tkinter bleibt nur die Konsole
        pass


def gui_starten() -> int:
    """Startet die Oberfläche."""
    global _tk, _ttk
    try:
        import tkinter as _tk
        from tkinter import ttk as _ttk
    except ImportError:
        startfehler_melden("Fehler: Tkinter ist nicht verfügbar. / "
                           "Error: Tkinter is not available.")
        return 2

    einstellungen = load_config()
    _.language = startup_language(einstellungen)
    apply_theme(einstellungen.get("theme") if einstellungen.get("theme") in THEMES
                else DEFAULT_THEME)
    widgets_bereitstellen()

    skalierung = dpi_bewusstsein_aktivieren()
    wurzel = _tk.Tk()
    if skalierung > 1.0:
        # Schriftgroessen sind in Punkt angegeben und muessen mitwachsen.
        wurzel.tk.call("tk", "scaling", skalierung * 96.0 / 72.0)
    icons_bestimmen(wurzel)
    fenstersymbol_setzen(wurzel)
    ManagerApp(wurzel)
    wurzel.mainloop()
    return 0


def main() -> int:
    return gui_starten()


# --------------------------------------------------------------------------
# SPRACHTABELLE / LANGUAGE TABLE
#
# Quellsprache ist Deutsch - der deutsche Text im Code ist zugleich der
# Schluessel. Eine weitere Sprache kommt in drei Schritten dazu:
#   1. Kuerzel und Anzeigename in LANGUAGE_NAMES eintragen,
#      z. B.  "fr": "Francais"
#   2. In TRANSLATIONS einen Eintrag "fr": { ... } anlegen und die
#      gewuenschten Zeilen uebersetzen.
#   3. Fertig - die Auswahl oben rechts zeigt die Sprache sofort an.
#
# Nicht uebersetzte Zeilen erscheinen automatisch auf Deutsch, eine
# unvollstaendige Tabelle ist also unproblematisch. Platzhalter in
# geschweiften Klammern - {anzahl}, {name}, {python} ... - muessen in der
# Uebersetzung unveraendert vorkommen; ihre Reihenfolge im Satz ist frei.
# --------------------------------------------------------------------------

LANGUAGE_NAMES = {
    "de": "Deutsch",
    "en": "English",
}

TRANSLATIONS = {
    "en": {
        # Kopfzeile, Reiter, Status
        "Version {version}": "Version {version}",
        "Sprache & Darstellung": "Language & appearance",
        "Dunkel": "Dark",
        "Scripts": "Scripts",
        "Module": "Modules",
        "Info & Copyright": "About & copyright",
        "Bereit.": "Ready.",
        "Letzte Aktion ({zeit}): {text}": "Last action ({zeit}): {text}",
        "Interner Fehler: {fehler}": "Internal error: {fehler}",
        "Die Einstellungen konnten nicht gespeichert werden: {pfad}":
            "The settings could not be saved: {pfad}",

        # Allgemeine Schalter
        "OK": "OK",
        "Abbrechen": "Cancel",
        "Schließen": "Close",
        "Weiter": "Next",
        "Kopieren": "Copy",
        "Leeren": "Clear",
        "Info": "Info",
        "In die Zwischenablage kopieren": "Copy to clipboard",
        "Auswahl kopieren": "Copy selection",
        "Alles kopieren": "Copy all",
        "Alle Dateien": "All files",

        # Reiter Scripts
        "Python-Scripts": "Python scripts",
        "Script hinzufügen": "Add script",
        "Abhängigkeiten prüfen": "Check dependencies",
        "Liest die Importe aller Scripts neu ein und prüft sie gegen die gewählte "
        "Installation.":
            "Re-reads the imports of all scripts and checks them against the selected "
            "installation.",
        "Zeitplan": "Schedule",
        "Ausführen mit": "Run with",
        "(noch nicht gesucht)": "(not searched yet)",
        "Vorherige Seite": "Previous page",
        "Nächste Seite": "Next page",
        "Seite {seite} von {seiten} · {anzahl} Scripts":
            "Page {seite} of {seiten} · {anzahl} scripts",
        "Noch keine Scripts – „Script hinzufügen“ nimmt das erste auf.":
            "No scripts yet – “Add script” adds the first one.",
        "Script entfernen": "Remove script",
        "Abhängigkeiten anzeigen": "Show dependencies",
        "Namen bearbeiten": "Edit name",
        "Script starten": "Run script",
        "Dieses Script steht schon in der Liste.": "This script is already in the list.",
        "Unter welchem Namen soll das Script in der Liste stehen?":
            "Under which name should the script appear in the list?",
        "Hinzufügen": "Add",
        "„{name}“ hinzugefügt.": "Added “{name}”.",
        "Neuer Name für „{name}“:": "New name for “{name}”:",
        "Übernehmen": "Apply",
        "„{name}“ aus der Liste entfernen? Die Datei selbst bleibt unangetastet.":
            "Remove “{name}” from the list? The file itself stays untouched.",
        "Entfernen": "Remove",
        "Abhängigkeiten aller Scripts neu geprüft.": "Dependencies of all scripts checked again.",

        # Tooltip und Abhaengigkeiten
        "Pfad: {pfad}": "Path: {pfad}",
        "Geprüft gegen: {python}": "Checked against: {python}",
        "keine Installation gefunden": "no installation found",
        "Die Datei wurde nicht gefunden.": "The file was not found.",
        "Syntaxfehler in Zeile {zeile}: {meldung}": "Syntax error in line {zeile}: {meldung}",
        "Standardbibliothek": "Standard library",
        "Installierte Module": "Installed modules",
        "Lokale Module": "Local modules",
        "Lokale Module (neben dem Script)": "Local modules (next to the script)",
        "Fehlende Module": "Missing modules",
        "Optionale Module (fehlen, werden aber abgefangen)":
            "Optional modules (missing, but handled by the script)",
        "Optional, nicht vorhanden": "Optional, not present",
        "FEHLEND ({anzahl}):": "MISSING ({anzahl}):",
        "… und {anzahl} weitere": "… and {anzahl} more",
        "(keine)": "(none)",
        "(ohne Paketdaten)": "(without package data)",
        "Die Module dieser Installation sind noch nicht eingelesen.":
            "The modules of this installation have not been read yet.",
        "Fehlende Module lassen sich über „Abhängigkeiten anzeigen“ oder im Reiter "
        "„Module“ installieren.":
            "Missing modules can be installed via “Show dependencies” or on the "
            "“Modules” tab.",
        "Keine Importe gefunden.": "No imports found.",
        "Alle Abhängigkeiten sind vorhanden.": "All dependencies are present.",
        "Doppelklick auf den Namen startet das Script.":
            "Double-click the name to run the script.",
        "Abhängigkeiten: {name}": "Dependencies: {name}",
        "Fehlende installieren …": "Install missing …",

        # Ausgabe
        "Script-Ausgabe": "Script output",
        "Stoppen": "Stop",
        "Beendet alle laufenden Scripts.": "Ends all running scripts.",
        "Fehlermeldungen kopieren": "Copy error messages",
        "Legt alle Fehlermeldungen seit dem letzten Leeren in die Zwischenablage.":
            "Puts all error messages since the output was last cleared on the clipboard.",
        "Datei nicht gefunden: {pfad}": "File not found: {pfad}",
        "Es wurde keine Python-Installation gefunden.": "No Python installation was found.",
        "Start: {name}": "Start: {name}",
        "Beendet: {name} – Exit-Code {code} nach {dauer} s":
            "Finished: {name} – exit code {code} after {dauer} s",
        "(gestoppt)": "(stopped)",
        "{anzahl} Script(s) laufen.": "{anzahl} script(s) running.",
        "Fehlermeldungen in die Zwischenablage kopiert.": "Error messages copied to the clipboard.",
        "[Stopp angefordert]": "[Stop requested]",

        # Zeitplan
        "Startet ein Script wiederholt im gewählten Abstand, solange dieses Programm läuft. "
        "Läuft das Script beim nächsten Termin noch, wird dieser Termin übersprungen.":
            "Runs a script repeatedly at the chosen interval for as long as this program is "
            "open. If the script is still running when the next run is due, that run is "
            "skipped.",
        "Script": "Script",
        "Abstand (Sekunden)": "Interval (seconds)",
        "Planen": "Schedule",
        "Aktive Pläne": "Active schedules",
        "Plan beenden": "End schedule",
        "{name} – alle {sekunden} s": "{name} – every {sekunden} s",
        "Bitte ein Script auswählen.": "Please select a script.",
        "Der Abstand muss eine ganze Zahl ab 5 sein.":
            "The interval must be a whole number of at least 5.",
        "„{name}“ startet jetzt alle {sekunden} s.":
            "“{name}” now runs every {sekunden} s.",
        "[Zeitplan] „{name}“ läuft noch – Termin übersprungen.":
            "[Schedule] “{name}” is still running – run skipped.",

        # Installationen
        "Suche Python-Installationen …": "Searching for Python installations …",
        "Lese Module ein: {python} …": "Reading modules: {python} …",
        "Fehler beim Einlesen: {fehler}": "Error while reading: {fehler}",
        "{anzahl} Installation(en) · Modullisten vom {zeit}":
            "{anzahl} installation(s) · module lists from {zeit}",
        "Modullisten noch nicht eingelesen": "Module lists not read yet",
        "Python-Installation hinzufügen": "Add Python installation",
        "Kommandozeile (PATH)": "command line (PATH)",
        "Doppelklick": "double-click",
        "dieses Programm": "this program",

        # Reiter Module
        "Liste aktualisieren": "Refresh list",
        "Liest die Module der gewählten Installation neu ein: neu installierte kommen hinzu, "
        "entfernte werden als fehlend markiert.":
            "Re-reads the modules of the selected installation: newly installed ones are "
            "added, removed ones are marked as missing.",
        "Alle Installationen neu einlesen": "Re-read all installations",
        "Sucht erneut nach Python-Installationen und liest ihre Module ein.":
            "Searches for Python installations again and reads their modules.",
        "Konsole öffnen": "Open console",
        "Öffnet eine Eingabeaufforderung, in der python und pip zur gewählten Installation "
        "gehören.":
            "Opens a command prompt in which python and pip belong to the selected "
            "installation.",
        "Installation hinzufügen …": "Add installation …",
        "Eine Installation oder virtuelle Umgebung von Hand aufnehmen, die die Suche nicht "
        "findet.":
            "Add an installation or virtual environment by hand that the search does not "
            "find.",
        "Modullisten aktualisieren": "Refresh module lists",
        "automatisch": "automatically",
        "durch Benutzer": "by the user",
        "Automatisch: bei jedem Programmstart und nach dem Schließen der Konsole.\n"
        "Durch Benutzer: nur beim ersten Start und auf Knopfdruck.":
            "Automatically: at every program start and after the console is closed.\n"
            "By the user: only at the first start and at the push of a button.",
        "Suche": "Search",
        "pip-Protokoll": "pip log",
        "Rechtsklick auf ein Modul öffnet alle Aktionen.":
            "Right-click a module for all actions.",
        "Die Python-Installationen werden gesucht …": "Searching for Python installations …",
        "Paket": "Package",
        "Version": "Version",
        "Status": "Status",
        "Importnamen": "Import names",
        "Benötigt": "Requires",
        "Benötigt von": "Required by",
        "installiert": "installed",
        "fehlt": "missing",
        "Stand: {zeit}": "As of: {zeit}",
        "{anzahl} Pakete": "{anzahl} package(s)",
        "pip fehlt": "pip missing",
        "Noch nicht eingelesen – „Liste aktualisieren“ liest die Module ein.":
            "Not read yet – “Refresh list” reads the modules.",
        "Script „{name}“": "script “{name}”",
        "Bitte zuerst ein Modul in der Liste auswählen.":
            "Please select a module in the list first.",
        "Modul hinzufügen": "Add module",
        "Modul hinzufügen …": "Add module …",
        "Name des Pakets, wie er bei pip install angegeben wird:":
            "Name of the package as given to pip install:",
        "Namen kopieren": "Copy name",
        "Aus der Liste entfernen": "Remove from list",
        "Hier gehören python und pip zu {python}. Beispiel: pip install paketname":
            "Here python and pip belong to {python}. Example: pip install packagename",
        "Konsole für {python} geöffnet.": "Console for {python} opened.",
        "Ordner öffnen": "Open folder",
        "Öffnet den Ordner der gewählten Installation im Explorer, python.exe ist dort markiert.":
            "Opens the folder of the selected installation in Explorer with python.exe "
            "selected.",
        "Der Ordner wurde nicht gefunden: {pfad}": "The folder was not found: {pfad}",
        "Ordner von {python} geöffnet.": "Opened the folder of {python}.",

        # Info-Fenster eines Moduls
        "Modul: {name}": "Module: {name}",
        "{python} – {status}": "{python} – {status}",
        "wird geladen …": "loading …",
        "Dieses Modul ist in der gewählten Installation nicht vorhanden.":
            "This module is not present in the selected installation.",
        "Installieren lässt es sich über den Schalter unten oder in der Konsole mit:":
            "It can be installed with the button below or in the console with:",

        # Installieren und Deinstallieren
        "Installieren": "Install",
        "Installieren …": "Install …",
        "Deinstallieren": "Uninstall",
        "Deinstallieren …": "Uninstall …",
        "Aktualisieren": "Upgrade",
        "Aktualisieren (Upgrade)": "Upgrade",
        "Bitte warten, bis der laufende Vorgang fertig ist.":
            "Please wait until the current operation has finished.",
        "Nur in {python}": "Only in {python}",
        "In allen kompatiblen Installationen ({anzahl})":
            "In all compatible installations ({anzahl})",
        "Modul installieren": "Install module",
        "Modul aktualisieren": "Upgrade module",
        "„{namen}“ installieren?": "Install “{namen}”?",
        "„{namen}“ auf die neueste Version aktualisieren?":
            "Upgrade “{namen}” to the latest version?",
        "In dieser Installation fehlt pip. Es lässt sich in der Konsole mit "
        "„python -m ensurepip“ nachrüsten.":
            "pip is missing in this installation. It can be added in the console with "
            "“python -m ensurepip”.",
        "Überall schon vorhanden – nichts zu tun.":
            "Already present everywhere – nothing to do.",
        "Modul deinstallieren": "Uninstall module",
        "„{name}“ ist in keiner Installation vorhanden.":
            "“{name}” is not present in any installation.",
        "Nur aus {python}": "Only from {python}",
        "Aus allen Installationen, die es enthalten ({anzahl})":
            "From all installations that contain it ({anzahl})",
        "{python}: wird noch gebraucht von {pakete}": "{python}: still required by {pakete}",
        "Diese Scripts verwenden es: {scripts}": "These scripts use it: {scripts}",
        "Achtung: {name} gehört zur Grundausstattung von Python. Ohne pip lassen sich keine "
        "Module mehr installieren.":
            "Caution: {name} is part of Python's basic equipment. Without pip no modules can "
            "be installed any more.",
        "„{name}“ wirklich deinstallieren? Das Modul bleibt als fehlend in der Liste und lässt "
        "sich von dort wieder installieren.":
            "Really uninstall “{name}”? The module stays in the list as missing and can be "
            "installed again from there.",
        "pip arbeitet …": "pip is working …",
        "✓ Erfolgreich: {befehl} [{python}]": "✓ Succeeded: {befehl} [{python}]",
        "✗ Fehlgeschlagen (nicht kompatibel oder nicht erreichbar): {befehl} [{python}]":
            "✗ Failed (not compatible or not reachable): {befehl} [{python}]",
        "pip meldet Fehler – Einzelheiten im pip-Protokoll.":
            "pip reports errors – details in the pip log.",
        "pip ist fertig.": "pip has finished.",

        # Reiter Info
        "Startet Python-Scripts mit sichtbarer Ausgabe, prüft vorab ihre Abhängigkeiten und "
        "verwaltet die Module jeder gefundenen Python-Installation.":
            "Runs Python scripts with visible output, checks their dependencies beforehand "
            "and manages the modules of every Python installation found.",
        "Erstellt mit Unterstützung von Claude AI": "Created with assistance of Claude AI",
        "Veröffentlicht unter der MIT-Lizenz.": "Released under the MIT licence.",
        "Technisches": "Technical details",
        "Python": "Python",
        "Tkinter": "Tkinter",
        "Einstellungen": "Settings",

        # Beenden
        "Programm beenden": "Quit program",
        "Es laufen noch {anzahl} Script(s). Beim Schließen werden sie beendet.":
            "{anzahl} script(s) are still running. Closing will end them.",
        "Scripts beenden und schließen": "End scripts and close",
    },
}


if __name__ == "__main__":
    sys.exit(main())
