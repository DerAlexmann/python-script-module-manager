"""Die Sprachtabelle - vollständig, mit passenden Platzhaltern, ohne Karteileichen."""

from __future__ import annotations

import ast
import re

from conftest import PROGRAMMDATEI


def schluessel_im_quelltext():
    """Alle Texte, die im Code mit _("...") übersetzt werden."""
    baum = ast.parse(PROGRAMMDATEI.read_text(encoding="utf-8"))
    gefunden = set()
    for knoten in ast.walk(baum):
        if (isinstance(knoten, ast.Call) and isinstance(knoten.func, ast.Name)
                and knoten.func.id == "_" and knoten.args):
            erstes = knoten.args[0]
            if isinstance(erstes, ast.Constant) and isinstance(erstes.value, str):
                gefunden.add(erstes.value)
    return gefunden


def alle_schluessel(pm):
    """Feste Schlüssel aus dem Quelltext plus die zur Laufzeit gebildeten."""
    return schluessel_im_quelltext() | set(pm.MARKEN.values())


def test_jede_sprache_ist_vollstaendig(pm):
    erwartet = alle_schluessel(pm)
    for sprache, tabelle in pm.TRANSLATIONS.items():
        fehlend = sorted(schluessel for schluessel in erwartet if schluessel not in tabelle)
        assert not fehlend, f"{sprache}: {fehlend}"


def test_keine_karteileichen(pm):
    erwartet = alle_schluessel(pm)
    for sprache, tabelle in pm.TRANSLATIONS.items():
        ueberzaehlig = sorted(schluessel for schluessel in tabelle if schluessel not in erwartet)
        assert not ueberzaehlig, f"{sprache}: {ueberzaehlig}"


def test_platzhalter_bleiben_erhalten(pm):
    for sprache, tabelle in pm.TRANSLATIONS.items():
        for deutsch, uebersetzt in tabelle.items():
            assert (set(re.findall(r"{(\w+)}", deutsch))
                    == set(re.findall(r"{(\w+)}", uebersetzt))), f"{sprache}: {deutsch!r}"


def test_jede_sprache_hat_einen_namen(pm):
    for sprache in pm.TRANSLATIONS:
        assert sprache in pm.LANGUAGE_NAMES
    assert pm.SOURCE_LANGUAGE in pm.LANGUAGE_NAMES


def test_uebersetzer_faellt_auf_deutsch_zurueck(pm):
    uebersetzer = pm.Translator("en")
    unbekannt = "Ein Text, den niemand übersetzt hat"
    assert uebersetzer(unbekannt) == unbekannt


def test_verschachtelte_texte_folgen_dem_sprachwechsel(pm):
    """Die Meldung "Letzte Aktion …" enthält selbst einen übersetzten Text."""
    vorher = pm._.language
    try:
        pm._.language = "de"
        innen = pm._("pip ist fertig.")
        text = pm._("Letzte Aktion ({zeit}): {text}").format(zeit="12:00:00", text=innen)
        pm._.language = "en"
        assert pm.tr(text) == "Last action (12:00:00): pip has finished."
    finally:
        pm._.language = vorher


def test_verfuegbare_sprachen_beginnen_mit_der_quellsprache(pm):
    namen = list(pm.Translator().available())
    assert namen[0] == pm.SOURCE_LANGUAGE
    assert set(namen) == {pm.SOURCE_LANGUAGE, *pm.TRANSLATIONS}
