# Mitmachen

Fehlermeldungen, Verbesserungsvorschläge und Übersetzungen sind willkommen.
Eine Änderung sollte das Programm einfacher zu bedienen machen, nicht nur
umfangreicher.

*English: this file is in German, but issues and pull requests in English are
just as welcome.*

## Einen Fehler melden

Ein [Issue](../../issues) mit Version (steht in der Kopfzeile und auf dem
Reiter „Info & Copyright"), Betriebssystem, Python-Fassung und dem, was du
erwartet hast. Bei Problemen mit einem Script hilft der Text aus
„Fehlermeldungen kopieren", bei Problemen mit pip der Inhalt des
pip-Protokolls. Sicherheitslücken gehören nicht ins Issue, sondern in eine
private Meldung – siehe [SECURITY.md](SECURITY.md).

## Das Projekt im Überblick

| Datei | Inhalt |
|---|---|
| `Python-Script & Module Manager.pyw` | das ganze Programm, eine Datei |
| `tests/` | Tests für Importerkennung, Einlesen, Sprachtabelle und Oberfläche |
| `build.cmd`, `icon_erzeugen.py` | EXE und Programmsymbol erzeugen |
| `.github/workflows/` | CI und das Bauen der Releases |

Die Programmdatei ist von oben nach unten gegliedert: Farbschemata,
Sprachumschaltung, Einstellungen, Unterprozesse, Suche nach
Python-Installationen, Einlesen der Module (`MODUL_PROBE`), Abhängigkeiten
eines Scripts, Bausteine der Oberfläche, Nebenfenster, die Klasse
`ManagerApp`, der Start – und ganz am Ende die Sprachtabelle.

`MODUL_PROBE` ist Quelltext, der **in der jeweiligen Installation** läuft,
nicht im Manager. Er muss deshalb auch unter älteren Python-Fassungen
funktionieren und darf nichts importieren, was nicht zur Standardbibliothek
gehört.

## Entwickeln

```bash
pip install -r requirements-dev.txt
python -m pytest tests -q
python -m ruff check .
```

Das Programm selbst braucht keine Pakete, nur Python mit Tkinter.

Die Tests der Oberfläche brauchen einen Bildschirm; ohne Anzeige überspringt
`pytest` sie von selbst. Sie arbeiten mit einer erfundenen Installation,
schreiben keine Einstellungsdatei und installieren oder deinstallieren nichts.

## Stil

- **Deutsch** in Kommentaren, Docstrings und Bezeichnern; englische Begriffe
  nur, wo sie die eingeführten sind (`FlatButton`, `pack`, `widget`).
- **Zeilenlänge 100**, vier Leerzeichen, keine Tabs. `ruff` prüft das.
- **Kommentare erklären das Warum**, nicht das Was.
- **Neue Texte** immer durch `_("…")` führen, sonst fehlen sie in der anderen
  Sprache. Ein Test achtet darauf.
- **Farben** nie direkt hinschreiben, sondern über die Rollen der
  Farbschemata (`faerben(widget, bg="CARD", fg="TEXT")`).
- **Tkinter nur aus dem Hauptthread** anfassen. Arbeit im Hintergrund meldet
  ihre Ergebnisse über `im_hauptthread(...)`.
- **Jede Deinstallation** läuft über `deinstallieren_anfragen()` und damit
  über die Rückfrage. Ein Test prüft das für alle Wege dorthin.

## Eine Sprache ergänzen

Deutsch ist die Quellsprache: Der deutsche Text im Code ist zugleich der
Schlüssel. Am Ende von `Python-Script & Module Manager.pyw`:

1. Kürzel und Anzeigename in `LANGUAGE_NAMES` eintragen, etwa
   `"fr": "Français"`.
2. In `TRANSLATIONS` einen Abschnitt `"fr": { … }` anlegen und übersetzen.
   Platzhalter in geschweiften Klammern – `{anzahl}`, `{name}`, `{python}` –
   müssen unverändert vorkommen; ihre Stellung im Satz ist frei.
3. `python -m pytest tests/test_uebersetzungen.py` sagt dir, was noch fehlt.

Nicht übersetzte Zeilen erscheinen automatisch auf Deutsch.

## Pull Requests

- Eine Änderung pro Pull Request, mit kurzer Begründung.
- Tests und `ruff` müssen durchlaufen; die CI prüft beides.
- Für sichtbare Änderungen einen Eintrag in `CHANGELOG.md` unter
  „Unveröffentlicht" ergänzen.
- Bildschirmfotos zeigen ausschließlich das Programmfenster – kein Desktop,
  keine anderen Fenster, keine persönlichen Pfade oder Paketlisten.

## Lizenz

Mit deinem Beitrag stimmst du zu, dass er unter der [MIT-Lizenz](LICENSE)
steht.
