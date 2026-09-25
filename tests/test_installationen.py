"""Einlesen einer echten Installation - der, unter der die Tests laufen.

Diese Tests starten den laufenden Interpreter als Unterprozess, verändern
aber nichts an ihm: MODUL_PROBE liest nur Paketdaten.
"""

from __future__ import annotations

import sys


def test_modul_probe_liefert_die_erwarteten_felder(pm):
    daten = pm.module_einlesen(sys.executable)
    assert "fehler" not in daten, daten.get("fehler")
    assert daten["version"] == ".".join(str(t) for t in sys.version_info[:3])
    assert {"os", "json", "tkinter"} <= set(daten["stdlib"])
    assert daten["pip"] is True
    assert daten["zeit"]
    for eintrag in daten["dists"]:
        assert {"name", "version", "top", "sub", "requires"} <= set(eintrag)


def test_pytest_wird_als_paket_erkannt(pm):
    index = pm.ModulIndex(pm.module_einlesen(sys.executable))
    assert index.ist_installiert("pytest")
    assert [p["name"].lower() for p in index.pakete_fuer("pytest")] == ["pytest"]


def test_die_eigene_installation_wird_gefunden(pm):
    gefunden = pm.installationen_finden()
    schluessel = {inst["key"] for inst in gefunden}
    assert pm.normschluessel(pm.konsolen_python(sys.executable)) in schluessel or any(
        # In einer virtuellen Umgebung meldet sich der Interpreter mit ihrem Pfad.
        "selbst" in inst["marken"] for inst in gefunden)
    assert len(schluessel) == len(gefunden), "eine Installation doppelt gelistet"


def test_kaputter_interpreter_liefert_einen_fehler(pm, tmp_path):
    daten = pm.module_einlesen(str(tmp_path / "gibt-es-nicht.exe"))
    assert "fehler" in daten
