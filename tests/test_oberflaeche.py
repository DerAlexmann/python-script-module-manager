"""Die Oberfläche: Seiten, Statusleiste, Umschalten, Scripts und Rückfragen."""

from __future__ import annotations

import sys

from conftest import alle_texte, warten


def scripts(tmp_path, anzahl):
    pfad = tmp_path / "leer.py"
    pfad.write_text("print('hallo')\n", encoding="utf-8")
    return [{"name": f"Script {n:02d}", "path": str(pfad)} for n in range(1, anzahl + 1)]


def test_baut_in_jeder_sprache_und_jedem_schema(pm, fenster, grund_cfg):
    for sprache in ("de", "en"):
        for schema in ("light", "dark"):
            app = fenster.bauen(grund_cfg, sprache, schema)
            assert app.master.cget("bg") == pm.THEMES[schema]["BG"]


def test_lange_liste_wird_auf_seiten_verteilt(pm, fenster, grund_cfg, tmp_path):
    grund_cfg["scripts"] = scripts(tmp_path, 40)
    app = fenster.bauen(grund_cfg)
    assert app.pro_seite >= 1
    assert app.seitenzahl() == -(-40 // app.pro_seite)
    assert app.seitenzahl() > 1
    zeilen = app.liste_rahmen.winfo_children()
    assert len(zeilen) == app.pro_seite
    assert str(app.knopf_zurueck["state"]) == "disabled"

    app.blaettern(1)
    assert app.seite == 1
    assert str(app.knopf_zurueck["state"]) == "normal"
    app.blaettern(99)
    assert app.seite == app.seitenzahl() - 1
    assert str(app.knopf_weiter["state"]) == "disabled"
    rest = 40 - app.seite * app.pro_seite
    assert len(app.liste_rahmen.winfo_children()) == rest


def test_meldung_blendet_sich_aus(pm, fenster, grund_cfg):
    app = fenster.bauen(grund_cfg)
    app.MELDUNG_MS = 200
    app.meldung(pm._("pip ist fertig."))
    assert app.var_status.get().startswith("Letzte Aktion (")
    assert warten(app.master, 3, bis=lambda: app.var_status.get() == "Bereit.")


def test_laufender_vorgang_verdraengt_die_meldung(pm, fenster, grund_cfg):
    app = fenster.bauen(grund_cfg)
    app.meldung(pm._("pip ist fertig."))
    app.status(pm._("pip arbeitet …"), verlauf=True)
    assert app.var_status.get() == "pip arbeitet …"
    app.status(pm._("Bereit."))
    assert app.var_status.get() == "Bereit."


def test_sprachwechsel_laesst_kein_deutsch_zurueck(pm, fenster, grund_cfg, tmp_path):
    grund_cfg["scripts"] = scripts(tmp_path, 3)
    app = fenster.bauen(grund_cfg, "de")
    app.sprache_setzen("en")
    app.master.update()
    deutsch = {k for k, v in pm.TRANSLATIONS["en"].items() if k != v and len(k) > 3}
    uebrig = [t for t in alle_texte(app.master) if t in deutsch]
    assert not uebrig, uebrig
    assert app.var_status.get() == "Ready."


def test_schemawechsel_faerbt_um(pm, fenster, grund_cfg, tmp_path):
    grund_cfg["scripts"] = scripts(tmp_path, 3)
    app = fenster.bauen(grund_cfg, schema="light")
    app.var_dunkel.set(True)
    app._schema_umgeschaltet()
    app.master.update()
    dunkel = pm.THEMES["dark"]
    assert app.master.cget("bg") == dunkel["BG"]
    zeile = app.liste_rahmen.winfo_children()[0]
    assert zeile.cget("bg") == dunkel["CARD_ALT"]
    hell = set(pm.THEMES["light"].values()) - set(dunkel.values())
    for widget, rollen in pm.GEFAERBTE_WIDGETS:
        if rollen:
            for option in rollen:
                assert str(widget.cget(option)) not in hell, (widget, option)


def test_modulliste_zeigt_installierte_und_fehlende(pm, fenster, grund_cfg):
    app = fenster.bauen(grund_cfg)
    schluessel = grund_cfg["installationen"][0]["key"]
    baum = app.modul_reiter_daten[schluessel]["baum"]
    assert set(baum.get_children()) == {"requests", "idna", "urllib3"}
    assert baum.set("urllib3", "status") == "fehlt"
    assert baum.set("idna", "benoetigt") == "requests"
    baum.item("requests", open=True)
    app._zweig_fuellen(schluessel, "requests")
    assert baum.get_children("requests") == ("requests/idna", "requests/urllib3")


def test_script_laeuft_und_fehler_lassen_sich_kopieren(pm, fenster, grund_cfg, tmp_path):
    pfad = tmp_path / "fehler.py"
    pfad.write_text("import sys\nprint('Ausgabe äöü')\nsys.exit('kaputt')\n", encoding="utf-8")
    grund_cfg["scripts"] = [{"name": "Fehlerscript", "path": str(pfad)}]
    app = fenster.bauen(grund_cfg)
    assert str(app.knopf_fehler["state"]) == "disabled"
    app.script_starten(grund_cfg["scripts"][0])
    assert warten(app.master, 20, bis=lambda: not app.laeufe)
    ausgabe = app.ausgabe.get("1.0", "end")
    assert "Ausgabe äöü" in ausgabe
    assert "kaputt" in ausgabe
    assert str(app.knopf_fehler["state"]) == "normal"
    app.fehler_kopieren()
    kopiert = app.master.clipboard_get()
    assert "Fehlerscript" in kopiert and "kaputt" in kopiert and "Exit-Code 1" in kopiert
    app.ausgabe_leeren()
    assert str(app.knopf_fehler["state"]) == "disabled"


def test_jede_deinstallation_fragt_nach(pm, fenster, grund_cfg, monkeypatch):
    """Abbrechen in der Rückfrage darf nichts deinstallieren - egal woher der Auftrag kam."""
    app = fenster.bauen(grund_cfg)
    schluessel = grund_cfg["installationen"][0]["key"]
    fragen = []

    class Abbrechen:
        def __init__(self, _app, titel, *args, **kwargs):
            fragen.append(str(titel))
            self.ergebnis, self.option, self.eingabe_text = None, None, ""

    auftraege = []
    monkeypatch.setattr(pm, "Dialog", Abbrechen)
    monkeypatch.setattr(app, "pip_ausfuehren", auftraege.append)

    app.deinstallieren_anfragen("requests", schluessel)          # Schalter und Kontextmenü
    baum = app.modul_reiter_daten[schluessel]["baum"]
    app.modul_reiter.select(app.modul_reiter_daten[schluessel]["seite"])
    baum.selection_set("idna")
    app._auswahl_deinstallieren()                                # Entf-Taste
    info = pm.ModulInfoFenster(app, schluessel, "requests")      # Info-Fenster
    info.fenster.destroy()
    app.deinstallieren_anfragen("requests", schluessel)

    assert fragen == ["Modul deinstallieren"] * 3
    assert auftraege == []


def test_zustimmung_startet_pip_uninstall(pm, fenster, grund_cfg, monkeypatch):
    app = fenster.bauen(grund_cfg)
    schluessel = grund_cfg["installationen"][0]["key"]

    class Zustimmen:
        def __init__(self, *args, **kwargs):
            self.ergebnis, self.option, self.eingabe_text = True, "eine", ""

    auftraege = []
    monkeypatch.setattr(pm, "Dialog", Zustimmen)
    monkeypatch.setattr(app, "pip_ausfuehren", auftraege.append)
    app.deinstallieren_anfragen("requests", schluessel)
    assert len(auftraege) == 1
    (inst, argumente, _beschreibung), = auftraege[0]
    assert inst["key"] == schluessel
    assert argumente == ["uninstall", "-y", "requests"]


def test_alte_scriptliste_wird_uebernommen(pm, fenster, grund_cfg, tmp_path, monkeypatch):
    alt = tmp_path / pm.ALTE_CONFIG
    alt.write_text('[{"name": "Altes Script", "path": "C:/x/alt.py"}]', encoding="utf-8")
    monkeypatch.setattr(pm, "programm_ordner", lambda: str(tmp_path))
    del grund_cfg["scripts"]
    app = fenster.bauen(grund_cfg)
    assert app.cfg["scripts"] == [{"name": "Altes Script", "path": "C:/x/alt.py"}]


def test_ausfuehren_mit_nutzt_die_gewaehlte_installation(pm, fenster, grund_cfg):
    app = fenster.bauen(grund_cfg)
    assert app.ausfuehrende_installation()["exe"] == pm.konsolen_python(sys.executable)
    assert app.python_feld.get() == "Python 3.12.0 · Python312"
