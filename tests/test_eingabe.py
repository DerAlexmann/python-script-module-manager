"""Scripts, die Eingaben lesen, und Modullisten, die nach einer Installation veralten."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap

import pytest
from conftest import modul_daten, paket, warten


def script(tmp_path, quelltext, name="script.py"):
    pfad = tmp_path / name
    pfad.write_text(textwrap.dedent(quelltext), encoding="utf-8")
    return str(pfad)


# -- Welche Eingabe braucht ein Script? -------------------------------------------

@pytest.mark.parametrize("quelltext, erwartet", [
    ("print('nur Ausgabe')\n", None),
    ("x = input('Zahl: ')\n", "zeile"),
    ("import sys\ndaten = sys.stdin.read()\n", "zeile"),
    ("import sys as s\nfor z in s.stdin:\n    pass\n", "zeile"),
    ("from sys import stdin\nstdin.readline()\n", "zeile"),
    ("import getpass\ngetpass.getpass()\n", "konsole"),
    ("import getpass as gp\ngp.getpass()\n", "konsole"),
    ("from getpass import getpass as frage\nfrage()\n", "konsole"),
    ("import msvcrt\nmsvcrt.getwch()\n", "konsole"),
    ("import curses\n", "konsole"),
    ("from msvcrt import getwch\ngetwch()\n", "konsole"),
    # Fremde Objekte mit gleichnamigen Teilen sind keine Eingabe
    ("import subprocess\nproc = subprocess.Popen(['x'])\nproc.stdin.write(b'')\n", None),
    ("class Formular:\n    def input(self): ...\nFormular().input()\n", None),
    # Nur den Benutzernamen holen fragt nichts ab
    ("import getpass\nprint(getpass.getuser())\n", None),
    # Konsole gewinnt, egal in welcher Reihenfolge
    ("input()\nimport getpass\ngetpass.getpass()\n", "konsole"),
    ("import getpass\ngetpass.getpass()\ninput()\n", "konsole"),
])
def test_eingabeart_wird_erkannt(pm, tmp_path, quelltext, erwartet):
    _funde, fehler, eingabe = pm.importe_lesen(script(tmp_path, quelltext))
    assert fehler is None
    assert eingabe == erwartet


# -- Ausgabe in Stuecken ------------------------------------------------------------

def test_dekoder_setzt_geteilte_zeichen_und_zeilenenden_zusammen(pm):
    dekoder = pm.StromDekoder()
    text = "Zahl äö\r\nnächste\rletzte\r\n".encode()
    teile = [text[:6], text[6:7], text[7:9], text[9:10], text[10:21], text[21:]]
    assert b"".join(teile) == text
    ergebnis = "".join(dekoder.stueck(t) for t in teile) + dekoder.ende()
    assert ergebnis == "Zahl äö\nnächste\nletzte\n"


def test_dekoder_gibt_eine_frage_ohne_zeilenende_sofort_heraus(pm):
    dekoder = pm.StromDekoder()
    assert dekoder.stueck(b"Gib eine Zahl ein: ") == "Gib eine Zahl ein: "


def test_dekoder_schliesst_ein_offenes_cr_am_ende_ab(pm):
    dekoder = pm.StromDekoder()
    assert dekoder.stueck(b"fertig\r") == "fertig"
    assert dekoder.ende() == "\n"


def test_praefix_nur_am_zeilenanfang(pm):
    text, anfang = pm.praefix_einfuegen("Zahl: ", "[A] ", True)
    assert (text, anfang) == ("[A] Zahl: ", False)
    text, anfang = pm.praefix_einfuegen("7\nzwei\n", "[A] ", anfang)
    assert (text, anfang) == ("7\n[A] zwei\n", True)
    text, anfang = pm.praefix_einfuegen("drei", "[A] ", anfang)
    assert (text, anfang) == ("[A] drei", False)


# -- Konsolenfenster ----------------------------------------------------------------

def konsolenstart(pm, pfad, cwd):
    """KONSOLEN_START ohne neues Fenster ausfuehren; stdin leer, damit es nicht wartet."""
    return subprocess.run(
        [sys.executable, "-c", pm.KONSOLEN_START, pfad, "Ende."], capture_output=True,
        text=True, encoding="utf-8", stdin=subprocess.DEVNULL, timeout=60, cwd=cwd)


def test_konsolenstart_verhaelt_sich_wie_ein_direkter_aufruf(pm, tmp_path):
    # Das Arbeitsverzeichnis liegt bewusst woanders: Den Nachbarn muss Python
    # ueber den Ordner des Scripts finden, wie bei "python script.py".
    ordner = tmp_path / "scripts"
    ordner.mkdir()
    script(ordner, "WERT = 42\n", name="nachbar.py")
    pfad = script(ordner, """\
        import sys
        import nachbar
        print(__name__, nachbar.WERT, sys.argv[0])
        sys.exit(3)
        """)
    ergebnis = konsolenstart(pm, pfad, cwd=tmp_path)
    assert ergebnis.stdout.split("\n")[0] == f"__main__ 42 {pfad}", ergebnis.stderr
    assert ergebnis.returncode == 3
    assert "Ende." in ergebnis.stdout


def test_konsolenstart_zeigt_fehler_und_meldet_exit_1(pm, tmp_path):
    ergebnis = konsolenstart(pm, script(tmp_path, "raise RuntimeError('kaputt')\n"),
                             cwd=tmp_path)
    assert "RuntimeError: kaputt" in ergebnis.stderr
    assert ergebnis.returncode == 1


def test_konsolenscript_startet_im_eigenen_fenster(pm, fenster, grund_cfg, tmp_path,
                                                   monkeypatch):
    pfad = script(tmp_path, "import getpass\ngetpass.getpass()\n")
    grund_cfg["scripts"] = [{"name": "Geheim", "path": pfad}]
    app = fenster.bauen(grund_cfg)
    aufrufe = []
    echtes_popen = subprocess.Popen

    def popen(befehl, **optionen):
        aufrufe.append((befehl, optionen))
        return echtes_popen([sys.executable, "-c", "raise SystemExit(1)"])   # Absturz
    monkeypatch.setattr(pm.subprocess, "Popen", popen)
    app.script_starten(grund_cfg["scripts"][0])
    befehl, optionen = aufrufe[0]
    assert befehl[1:4] == ["-c", pm.KONSOLEN_START, pfad]
    assert optionen["creationflags"] == pm.NEUE_KONSOLE
    assert "stdout" not in optionen                  # Ausgabe bleibt im Konsolenfenster
    assert str(app.eingabe_feld["state"]) == "disabled"
    assert warten(app.master, 20, bis=lambda: not app.laeufe)
    # Das Fehlerprotokoll sagt, wo die Fehlermeldung zu finden war
    assert "Die Ausgabe stand im eigenen Konsolenfenster." in app.fehlerprotokoll[-1]


# -- Eingabezeile der App -----------------------------------------------------------

def test_eingabe_erreicht_das_laufende_script(pm, fenster, grund_cfg, tmp_path):
    pfad = script(tmp_path, """\
        zahl = int(input("Gib eine Zahl ein: "))
        print("doppelt:", zahl * 2)
        """)
    grund_cfg["scripts"] = [{"name": "Rechner", "path": pfad}]
    app = fenster.bauen(grund_cfg)
    assert str(app.eingabe_feld["state"]) == "disabled"
    app.script_starten(grund_cfg["scripts"][0])

    # Die Frage steht da, bevor etwas eingegeben wurde
    assert warten(app.master, 20, bis=lambda: "Gib eine Zahl ein: " in app.ausgabe.get(
        "1.0", "end"))
    assert str(app.eingabe_feld["state"]) == "normal"
    assert app.eingabe_ziel.get() == "Rechner"
    app.var_script_eingabe.set("21")
    app.eingabe_senden()
    assert app.var_script_eingabe.get() == ""

    assert warten(app.master, 20, bis=lambda: not app.laeufe)
    ausgabe = app.ausgabe.get("1.0", "end")
    assert "Gib eine Zahl ein: 21\n" in ausgabe          # Eingabe steht hinter der Frage
    assert "doppelt: 42" in ausgabe
    assert "Exit-Code 0" in ausgabe
    assert not app.fehlerprotokoll
    assert str(app.eingabe_feld["state"]) == "disabled"
    # kein Fokus auf gesperrtem Feld - auch nicht beim naechsten Aktivieren des Fensters
    assert app.master.focus_lastfor() is not app.eingabe_feld


def test_ende_schliesst_die_eingabe(pm, fenster, grund_cfg, tmp_path):
    pfad = script(tmp_path, """\
        import sys
        print("Zeilen:", len(sys.stdin.read().splitlines()))
        """)
    grund_cfg["scripts"] = [{"name": "Leser", "path": pfad}]
    app = fenster.bauen(grund_cfg)
    app.script_starten(grund_cfg["scripts"][0])
    for zeile in ("eins", "zwei"):
        app.var_script_eingabe.set(zeile)
        app.eingabe_senden()
    app.eingabe_schliessen()
    assert warten(app.master, 20, bis=lambda: not app.laeufe)
    ausgabe = app.ausgabe.get("1.0", "end")
    assert "Zeilen: 2" in ausgabe
    assert "Exit-Code 0" in ausgabe


def test_eingabe_geht_an_das_gewaehlte_script(pm, fenster, grund_cfg, tmp_path):
    frage = """\
        antwort = input("{name}? ")
        print("{name} bekam", antwort)
        """
    grund_cfg["scripts"] = [
        {"name": n, "path": script(tmp_path, frage.format(name=n), name=f"{n}.py")}
        for n in ("Erstes", "Zweites")]
    app = fenster.bauen(grund_cfg)
    for eintrag in grund_cfg["scripts"]:
        app.script_starten(eintrag)
    # Das zuletzt gestartete Script mit Eingaben ist vorgewaehlt
    assert app.eingabe_ziel.get() == "Zweites"
    assert sorted(app.eingabe_ziel["values"]) == ["Erstes", "Zweites"]
    app.eingabe_ziel.set("Erstes")
    # Ein weiteres Script ohne Fragen (etwa aus dem Zeitplan) aendert die Wahl nicht
    stumm = {"name": "Stumm", "path": script(tmp_path, "import time\ntime.sleep(1)\n",
                                             name="stumm.py")}
    app.script_starten(stumm)
    assert app.eingabe_ziel.get() == "Erstes"
    app.var_script_eingabe.set("a")
    app.eingabe_senden()
    assert warten(app.master, 20, bis=lambda: "Erstes" not in app.eingabe_ziel["values"])
    assert app.eingabe_ziel.get() == "Zweites"
    app.var_script_eingabe.set("b")
    app.eingabe_senden()
    assert warten(app.master, 20, bis=lambda: not app.laeufe)
    ausgabe = app.ausgabe.get("1.0", "end")
    assert "Erstes bekam a" in ausgabe
    assert "Zweites bekam b" in ausgabe


def test_umlaute_kommen_unversehrt_an(pm, fenster, grund_cfg, tmp_path):
    pfad = script(tmp_path, "print(repr(input()))\n")
    grund_cfg["scripts"] = [{"name": "Echo", "path": pfad}]
    app = fenster.bauen(grund_cfg)
    app.script_starten(grund_cfg["scripts"][0])
    app.var_script_eingabe.set("Grüße ✓")
    app.eingabe_senden()
    assert warten(app.master, 20, bis=lambda: not app.laeufe)
    assert "'Grüße ✓'" in app.ausgabe.get("1.0", "end")


def test_geschlossene_eingabe_wird_gemeldet(pm, fenster, grund_cfg, tmp_path, monkeypatch):
    pfad = script(tmp_path, "import time\ntime.sleep(5)\n")
    grund_cfg["scripts"] = [{"name": "Schlaefer", "path": pfad}]
    app = fenster.bauen(grund_cfg)
    meldungen = []
    monkeypatch.setattr(app, "meldung", lambda text, fehler=False: meldungen.append(
        (pm.tr(text), fehler)))
    app.script_starten(grund_cfg["scripts"][0])
    lauf = next(iter(app.laeufe.values()))
    lauf["prozess"].stdin.close()                    # Pipe weg, App weiss es noch nicht
    app.var_script_eingabe.set("verloren?")
    app.eingabe_senden()
    assert meldungen == [("„Schlaefer“ nimmt keine Eingaben mehr an.", True)]
    assert app.var_script_eingabe.get() == "verloren?"        # Text geht nicht verloren
    assert str(app.eingabe_feld["state"]) == "disabled"
    app.scripts_stoppen()
    assert warten(app.master, 20, bis=lambda: not app.laeufe)


def test_gleichnamige_scripts_werden_unterschieden(pm, fenster, grund_cfg, tmp_path):
    eintrag = {"name": "Frage", "path": script(tmp_path, """\
        import sys
        antwort = input("Frage? ")
        print("bekam", antwort)
        sys.stdin.read()
        """)}
    grund_cfg["scripts"] = [eintrag]
    app = fenster.bauen(grund_cfg)
    app.script_starten(eintrag)
    app.script_starten(eintrag)
    erster, zweiter = sorted(app.laeufe)
    assert sorted(app.eingabe_ziel["values"]) == [f"Frage #{erster}", f"Frage #{zweiter}"]
    app.eingabe_ziel.set(f"Frage #{erster}")
    app.var_script_eingabe.set("a")
    app.eingabe_senden()
    # Endet der zweite Lauf, bleibt die Wahl beim ersten - jetzt ohne Nummer
    app.eingabe_ziel.set(f"Frage #{zweiter}")
    app.eingabe_schliessen()
    app.eingabe_ziel.set(f"Frage #{erster}")
    assert warten(app.master, 20, bis=lambda: len(app.laeufe) == 1)
    assert list(app.eingabe_ziel["values"]) == ["Frage"]
    assert app.eingabe_ziel.get() == "Frage"
    assert warten(app.master, 20, bis=lambda: "bekam a" in app.ausgabe.get("1.0", "end"))
    app.eingabe_schliessen()
    assert warten(app.master, 20, bis=lambda: not app.laeufe)


def test_praefixe_bei_mehreren_laeufen(pm, fenster, grund_cfg, tmp_path):
    # Beide Scripts bleiben am Leben, bis ihre Eingabe geschlossen wird - so
    # laufen waehrend der Pruefung sicher zwei, und jede Zeile traegt ein Praefix.
    quelltext = ('import sys\nprint("{name} bereit")\nantwort = input()\n'
                 'print("{name} bekam", antwort)\nsys.stdin.read()\n')
    grund_cfg["scripts"] = [
        {"name": n, "path": script(tmp_path, quelltext.format(name=n), name=f"{n}.py")}
        for n in ("Erstes", "Zweites")]
    app = fenster.bauen(grund_cfg)
    for eintrag in grund_cfg["scripts"]:
        app.script_starten(eintrag)
    assert warten(app.master, 20, bis=lambda: "Zweites bereit" in app.ausgabe.get(
        "1.0", "end") and "Erstes bereit" in app.ausgabe.get("1.0", "end"))
    for name, antwort in (("Erstes", "a"), ("Zweites", "b")):
        app.eingabe_ziel.set(name)
        app.var_script_eingabe.set(antwort)
        app.eingabe_senden()
        assert warten(app.master, 20, bis=lambda n=name: f"{n} bekam" in app.ausgabe.get(
            "1.0", "end"))
    zeilen = app.ausgabe.get("1.0", "end").split("\n")
    for zeile in ("[Erstes] a", "[Erstes] Erstes bekam a", "[Zweites] b",
                  "[Zweites] Zweites bekam b"):
        assert zeile in zeilen
    assert not any("] [" in zeile for zeile in zeilen)     # nie zwei Praefixe
    for name in ("Erstes", "Zweites"):
        app.eingabe_ziel.set(name)
        app.eingabe_schliessen()
    assert warten(app.master, 20, bis=lambda: not app.laeufe)


def test_fehler_in_stuecken_landen_vollstaendig_im_protokoll(pm, fenster, grund_cfg, tmp_path):
    pfad = script(tmp_path, """\
        import sys, time
        sys.stderr.write("erster Teil ")
        sys.stderr.flush()
        time.sleep(0.3)
        sys.stderr.write("zweiter Teil\\nzweite Zeile\\n")
        sys.exit(2)
        """)
    grund_cfg["scripts"] = [{"name": "Stueckchen", "path": pfad}]
    app = fenster.bauen(grund_cfg)
    app.script_starten(grund_cfg["scripts"][0])
    assert warten(app.master, 20, bis=lambda: not app.laeufe)
    block = app.fehlerprotokoll[-1].split("\n")
    assert block[-3:] == ["erster Teil zweiter Teil", "zweite Zeile", "Exit-Code 2"]


# -- Veraltete Modullisten ----------------------------------------------------------

def test_aenderung_im_paketordner_macht_die_liste_veraltet(pm, tmp_path):
    ordner = tmp_path / "site-packages"
    ordner.mkdir()
    fehlt_noch = tmp_path / "user-site-packages"
    daten = modul_daten([])
    daten["stempel"] = pm.orte_stempel([str(ordner), str(fehlt_noch)])
    assert daten["stempel"][str(fehlt_noch)] is None
    assert not pm.module_veraltet(daten)

    (ordner / "pandas").mkdir()
    stand = os.stat(ordner).st_mtime_ns
    os.utime(ordner, ns=(stand + 10**9, stand + 10**9))   # grobe Zeitaufloesung umgehen
    assert pm.module_veraltet(daten)

    daten["stempel"] = pm.orte_stempel(daten["stempel"])
    assert not pm.module_veraltet(daten)
    fehlt_noch.mkdir()                                     # erstes pip install --user
    assert pm.module_veraltet(daten)


def test_daten_aelterer_versionen_gelten_als_veraltet(pm):
    alt = modul_daten([paket("pandas")])
    del alt["stempel"]
    assert pm.module_veraltet(alt)
    assert not pm.module_veraltet(None)
    assert not pm.module_veraltet({"fehler": "Timeout"})


def test_veraltete_installation_wird_neu_eingelesen(pm, fenster, grund_cfg, monkeypatch):
    app = fenster.bauen(grund_cfg)
    schluessel = grund_cfg["ausfuehren_mit"]
    eingelesen = []
    monkeypatch.setattr(app, "installationen_einlesen", eingelesen.append)

    app.veraltete_nachlesen()
    assert eingelesen == []                               # nichts geaendert, nichts zu tun

    del app.cfg["modul_daten"][schluessel]["stempel"]
    app.veraltete_nachlesen()
    assert eingelesen == [[schluessel]]


def test_start_und_abhaengigkeitspruefung_lesen_veraltetes_nach(pm, fenster, grund_cfg,
                                                               monkeypatch):
    schluessel = grund_cfg["ausfuehren_mit"]
    del grund_cfg["modul_daten"][schluessel]["stempel"]
    eingelesen = []
    monkeypatch.setattr(pm.ManagerApp, "installationen_einlesen",
                        lambda self, liste: eingelesen.append(liste))
    app = fenster.bauen(grund_cfg)                        # Einstellung "manuell"
    assert eingelesen == [[schluessel]]
    assert app.master.bind("<Activate>")                  # Rueckkehr ins Fenster prueft auch
    app.abhaengigkeiten_neu_pruefen()
    assert eingelesen == [[schluessel], [schluessel]]


def test_tooltip_nennt_den_weg_fuer_eingaben(pm, fenster, grund_cfg, tmp_path):
    grund_cfg["scripts"] = [
        {"name": "Frage", "path": script(tmp_path, "input()\n", name="frage.py")},
        {"name": "Geheim", "path": script(tmp_path, "import getpass\ngetpass.getpass()\n",
                                          name="geheim.py")}]
    app = fenster.bauen(grund_cfg)
    assert "„Eingabe an“" in app.script_tooltip(grund_cfg["scripts"][0])
    assert "Konsolenfenster" in app.script_tooltip(grund_cfg["scripts"][1])


def test_fehlgeschlagenes_nachlesen_wird_nicht_endlos_wiederholt(pm, fenster, grund_cfg,
                                                                 tmp_path):
    app = fenster.bauen(grund_cfg)
    schluessel = grund_cfg["ausfuehren_mit"]
    ordner = tmp_path / "site-packages"
    ordner.mkdir()
    app.cfg["modul_daten"][schluessel]["stempel"] = {str(ordner): 1}   # veraltet
    assert pm.module_veraltet(app.cfg["modul_daten"][schluessel])
    app._daten_uebernehmen(schluessel, {"fehler": "Timeout"})
    assert not pm.module_veraltet(app.cfg["modul_daten"][schluessel])
    assert app.cfg["modul_daten"][schluessel]["dists"]          # alte Liste bleibt erhalten


def test_rueckkehr_ins_fenster_prueft_hoechstens_alle_fuenf_sekunden(pm, fenster, grund_cfg,
                                                                     monkeypatch):
    app = fenster.bauen(grund_cfg)
    geprueft = []
    monkeypatch.setattr(app, "veraltete_nachlesen", lambda: geprueft.append(1))

    class Ereignis:
        widget = app.master

    app._modulstand_geprueft = 0.0
    app._fenster_aktiviert(Ereignis())
    assert geprueft == [1]
    app._modulstand_geprueft = pm.time.monotonic()
    app._fenster_aktiviert(Ereignis())
    assert geprueft == [1]
    Ereignis.widget = app.ausgabe                       # Kind-Widgets zaehlen nicht
    app._modulstand_geprueft = 0.0
    app._fenster_aktiviert(Ereignis())
    assert geprueft == [1]
