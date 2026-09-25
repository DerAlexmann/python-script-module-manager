"""Importe eines Scripts erkennen und den Paketen einer Installation zuordnen."""

from __future__ import annotations

import textwrap

from conftest import modul_daten, paket


def script(tmp_path, quelltext, name="script.py"):
    pfad = tmp_path / name
    pfad.write_text(textwrap.dedent(quelltext), encoding="utf-8")
    return str(pfad)


def funde(pm, tmp_path, quelltext):
    gefunden, syntaxfehler = pm.importe_lesen(script(tmp_path, quelltext))
    assert syntaxfehler is None
    return gefunden


# -- Importe lesen -----------------------------------------------------------

def test_einfache_und_verschachtelte_importe(pm, tmp_path):
    gefunden = funde(pm, tmp_path, """
        import os, sys
        import xml.etree.ElementTree as ET
        from google.cloud import storage
    """)
    assert {"os", "sys", "xml.etree.ElementTree", "google.cloud"} <= set(gefunden)
    assert gefunden["google.cloud"]["kandidaten"] == {"google.cloud.storage"}


def test_relative_importe_und_future_zaehlen_nicht(pm, tmp_path):
    gefunden = funde(pm, tmp_path, """
        from __future__ import annotations
        from . import nachbar
        from .paket import etwas
    """)
    assert gefunden == {}


def test_type_checking_wird_uebergangen(pm, tmp_path):
    gefunden = funde(pm, tmp_path, """
        from typing import TYPE_CHECKING
        if TYPE_CHECKING:
            import pandas
        else:
            import csv
    """)
    assert "pandas" not in gefunden
    assert "csv" in gefunden


def test_abgefangener_import_ist_optional(pm, tmp_path):
    gefunden = funde(pm, tmp_path, """
        try:
            import ujson as json
        except ImportError:
            import json
    """)
    assert gefunden["ujson"]["optional"] is True
    assert gefunden["json"]["optional"] is False     # der Ersatz selbst ist Pflicht


def test_abgefangen_aber_beendet_ist_pflicht(pm, tmp_path):
    """Ein except-Zweig, der das Script beendet, macht das Modul nicht optional."""
    gefunden = funde(pm, tmp_path, """
        import sys
        def main():
            try:
                import numpy
            except ImportError:
                return 2
        try:
            import yaml
        except ImportError:
            sys.exit("PyYAML fehlt")
        try:
            import toml
        except ModuleNotFoundError:
            raise SystemExit(1)
    """)
    for modul in ("numpy", "yaml", "toml"):
        assert gefunden[modul]["optional"] is False, modul


def test_pflicht_schlaegt_optional(pm, tmp_path):
    gefunden = funde(pm, tmp_path, """
        try:
            import requests
        except ImportError:
            requests = None
        import requests
    """)
    assert gefunden["requests"]["optional"] is False


def test_import_module_mit_festem_namen(pm, tmp_path):
    gefunden = funde(pm, tmp_path, """
        import importlib
        yaml = importlib.import_module("yaml")
        toml = __import__("toml")
        relativ = importlib.import_module(".relativ", "paket")
    """)
    assert {"yaml", "toml"} <= set(gefunden)
    assert ".relativ" not in gefunden


def test_syntaxfehler_wird_gemeldet(pm, tmp_path):
    gefunden, syntaxfehler = pm.importe_lesen(script(tmp_path, "def kaputt(:\n    pass\n"))
    assert gefunden == {}
    assert syntaxfehler[0] == 1


# -- Zuordnung zu Paketen -----------------------------------------------------

def index(pm, *pakete, toplevel=()):
    return pm.ModulIndex(modul_daten(list(pakete), toplevel))


def pruefen(pm, tmp_path, quelltext, idx, weitere=()):
    pfad = script(tmp_path, quelltext)
    gefunden, _fehler = pm.importe_lesen(pfad)
    return pm.abhaengigkeiten_pruefen(pfad, gefunden, idx, weitere)


def test_standardbibliothek_installiert_und_fehlend(pm, tmp_path):
    idx = index(pm, paket("pillow", "12.0", top=["PIL"]))
    ergebnis = pruefen(pm, tmp_path, """
        import os
        from PIL import Image
        import requests
    """, idx)
    assert ergebnis["stdlib"] == ["os"]
    assert ergebnis["extern"] == [("PIL", [("pillow", "12.0")])]
    assert ergebnis["fehlt"] == [("requests", "requests")]


def test_lokale_module_neben_dem_script(pm, tmp_path):
    (tmp_path / "helfer.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "werkzeug").mkdir()
    (tmp_path / "werkzeug" / "teil.py").write_text("", encoding="utf-8")
    ergebnis = pruefen(pm, tmp_path, """
        import helfer
        from werkzeug import teil
    """, index(pm))
    assert ergebnis["lokal"] == ["helfer", "werkzeug"]
    assert ergebnis["fehlt"] == []


def test_namensraum_pakete_werden_unterschieden(pm, tmp_path):
    """"google" teilen sich mehrere Pakete - entscheidend ist der Unterpfad."""
    idx = index(pm, paket("protobuf", "5.0", top=["google"],
                          sub=["google.protobuf", "google.protobuf.internal"]))
    ergebnis = pruefen(pm, tmp_path, """
        from google.protobuf import message
        from google.cloud import storage
    """, idx)
    assert ergebnis["extern"] == [("google.protobuf", [("protobuf", "5.0")])]
    assert ergebnis["fehlt"] == [("google.cloud", "google-cloud-storage")]


def test_importierbar_ohne_paketdaten(pm, tmp_path):
    ergebnis = pruefen(pm, tmp_path, "import altmodul\n", index(pm, toplevel=["altmodul"]))
    assert ergebnis["extern"] == [("altmodul", [])]


def test_vorschlag_aus_der_namenstabelle(pm, tmp_path):
    ergebnis = pruefen(pm, tmp_path, "import cv2\nimport win32api\n", index(pm))
    assert ergebnis["fehlt"] == [("cv2", "opencv-python"), ("win32api", "pywin32")]


def test_vorschlag_aus_einer_anderen_installation(pm, tmp_path):
    andere = index(pm, paket("Ein-Paket", "1.0", top=["einpaket"]))
    ergebnis = pruefen(pm, tmp_path, "import einpaket\n", index(pm), [andere])
    assert ergebnis["fehlt"] == [("einpaket", "Ein-Paket")]


def test_optional_fehlend_ist_keine_warnung(pm, tmp_path):
    ergebnis = pruefen(pm, tmp_path, """
        try:
            import ujson
        except ImportError:
            ujson = None
    """, index(pm))
    assert ergebnis["fehlt"] == []
    assert ergebnis["optional"] == [("ujson", "ujson")]


def test_ohne_eingelesene_daten_bleibt_alles_offen(pm, tmp_path):
    ergebnis = pruefen(pm, tmp_path, "import os\nimport requests\n", None)
    assert ergebnis["unbekannt"] == ["os", "requests"]


# -- Hilfen -------------------------------------------------------------------

def test_kanonische_paketnamen(pm):
    assert pm.kanon("Pillow_Heif") == "pillow-heif"
    assert pm.kanon("ruamel.yaml") == "ruamel-yaml"
    assert pm.kanon("zope..interface") == "zope-interface"


def test_rueckwaerts_abhaengigkeiten(pm):
    idx = index(pm, paket("requests", requires=["idna", "urllib3"]),
                paket("httpx", requires=["idna"]), paket("idna"))
    assert sorted(idx.rueck["idna"]) == ["httpx", "requests"]
    assert idx.ist_installiert("IDNA")
    assert not idx.ist_installiert("urllib3")


def test_pythonw_wird_zu_python(pm, tmp_path):
    (tmp_path / "python.exe").write_bytes(b"")
    (tmp_path / "pythonw.exe").write_bytes(b"")
    assert pm.konsolen_python(str(tmp_path / "pythonw.exe")) == str(tmp_path / "python.exe")
    assert pm.konsolen_python(str(tmp_path / "python.exe")) == str(tmp_path / "python.exe")


def test_store_platzhalter_werden_erkannt(pm):
    assert pm.ist_store_platzhalter(
        r"C:\Users\x\AppData\Local\Microsoft\WindowsApps\python.exe")
    assert not pm.ist_store_platzhalter(r"C:\Python312\python.exe")
