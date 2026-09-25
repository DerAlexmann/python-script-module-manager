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


def test_launcher_liste_mit_voreinstellung(pm):
    ausgabe = "\n".join([r" -V:3.14 *        C:\Python314\python.exe",
                         r" -V:3.12          C:\Python312\python.exe",
                         r" -3.10-64         C:\Alt\Python310\pythonw.exe"])
    pfade, standard = pm.launcher_liste_lesen(ausgabe)
    assert pfade == [r"C:\Python314\python.exe", r"C:\Python312\python.exe",
                     r"C:\Alt\Python310\pythonw.exe"]
    assert standard == r"C:\Python314\python.exe"


def test_launcher_liste_ohne_voreinstellung(pm):
    assert pm.launcher_liste_lesen(r" -V:3.12   C:\Python312\python.exe")[1] is None


def test_jede_installation_wird_nur_einmal_gestartet(pm, monkeypatch):
    """Suchen und Einlesen kosten zusammen genau einen Aufruf je Installation.

    Jeder Aufruf eines Interpreters wird von einem Virenschutz geprueft; beim
    ersten Start einer unbekannten EXE kann das die Suche stark bremsen.
    """
    aufrufe = []
    echt = pm.verdeckt_ausfuehren

    def zaehlen(befehl, *args, **kwargs):
        aufrufe.append(befehl)
        return echt(befehl, *args, **kwargs)

    monkeypatch.setattr(pm, "verdeckt_ausfuehren", zaehlen)
    module = {}
    gefunden = pm.installationen_finden(module=module)
    assert gefunden
    interpreter = [b for b in aufrufe if b[1:2] == ["-c"]]
    assert all(b[2] == pm.MODUL_PROBE for b in interpreter), "keine zusaetzliche Schnellabfrage"
    assert len(interpreter) <= len(gefunden) + 1, "hoechstens ein Umweg ueber eine Weiterleitung"
    for inst in gefunden:
        assert "dists" in module[inst["key"]]
