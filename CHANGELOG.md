# Änderungen

Das Format folgt [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
die Versionsnummern der [semantischen Versionierung](https://semver.org/lang/de/).

## [2.0.3] – 2026-10-31

Das Programm selbst ändert sich nicht, nur die Auslieferung der EXE.

### Hinzugefügt

- `DRITTANBIETER-LIZENZEN.md` und `NOTICE` nennen die Fremdkomponenten der EXE
  mit Lizenz und Quelle. Die Lizenzdatei liegt jedem Release bei, dort mit den
  vollständigen Texten von Python und PyInstaller.
- Die EXE trägt Produktname, Version und Urheber in den Dateieigenschaften.

### Geändert

- Die EXE entsteht mit einer festen PyInstaller-Fassung
  (`requirements-build.txt`). Das ist kein Hash-Pin, und mitgezogene
  Abhängigkeiten sind nicht festgelegt: Bit für Bit reproduzierbar ist der Bau
  also nicht.
- Der Release-Bau prüft jetzt, ob das Programmfenster erscheint und die Version
  der EXE zum Tag passt. Fehlende Dateien lassen ihn scheitern, und er lässt
  sich ohne Tag proben.

## [2.0.2] – 2026-10-12

### Sicherheit

- Die Abhängigkeitsprüfung übernimmt aus `import_module("…")` und
  `__import__("…")` nur noch echte Modulnamen. Bisher konnte ein Script dort
  zum Beispiel `--extra-index-url=…` hineinschreiben; der Text erschien als
  fehlendes Paket, und „Fehlende installieren“ hätte ihn als Option an pip
  weitergereicht, das dann auch auf einem fremden Server nach Paketen gesucht
  hätte.
- Paketnamen, die mit `-` beginnen, gibt das Programm grundsätzlich nicht
  mehr an `pip install` weiter, auch nicht aus „Modul hinzufügen“.

## [2.0.1] – 2026-09-26

### Geändert

- Die Suche nach Python-Installationen startet jede Installation nur noch
  einmal und liest dabei gleich ihre Module ein. Welche Installation ein
  Doppelklick startet, steht in der Liste von `py -0p`, die ohnehin gelesen
  wird. Auf einem Rechner mit zwei Installationen sinkt die Zahl der
  gestarteten Prozesse von neun auf drei. Das spürt man vor allem beim ersten
  Start der EXE, wenn ein Virenschutz jeden dieser Aufrufe prüft.

## [2.0.0] – 2026-09-25

Erste veröffentlichte Fassung. Sie ersetzt eine unveröffentlichte
Vorgängerfassung unter dem Namen „Script & Module Manager Pro"; deren
Script-Liste (`buttons_config.json` neben dem Programm) wird beim ersten Start
übernommen.

### Hinzugefügt

- Script-Liste mit dem Namen als Text, Statuspunkt und Symbol-Schaltern zum
  Starten, Umbenennen, Anzeigen der Abhängigkeiten und Entfernen; Tooltip mit
  den Einzelheiten.
- Seiten statt Rollbalken, umzuschalten mit ◀/▶ oder dem Mausrad.
- „Fehlermeldungen kopieren" für alle Fehlerausgaben seit dem letzten Leeren.
- Mehrere Scripts gleichzeitig; Auswahl der ausführenden Python-Installation.
- Abhängigkeitsprüfung, die Import- und Paketnamen unterscheidet, verschachtelte
  Module und Namensräume richtig zuordnet und lokale, relative, abgefangene
  und `TYPE_CHECKING`-Importe erkennt.
- Modulverwaltung mit einem Reiter je Python-Installation, Abhängigkeitsbaum,
  „Benötigt von", Installieren, Deinstallieren und Aktualisieren – per
  Schalter oder Rechtsklick, in einer oder allen Installationen.
- Rückfrage vor jeder Deinstallation, mit Warnung, wenn andere Pakete oder
  eigene Scripts das Modul brauchen.
- Deinstallierte Module bleiben als „fehlt" in der Liste und lassen sich dort
  wieder installieren.
- Modullisten automatisch oder nur auf Knopfdruck aktualisieren.
- Schalter „Konsole öffnen" und „Ordner öffnen" für die gewählte Installation.
- Zeitplan, der sich auch wieder beenden lässt.
- Deutsch und Englisch, helles und dunkles Schema.
- Fenster startet mittig und merkt sich Lage und Größe.
- Statusleiste mit „Letzte Aktion (Uhrzeit): …", die sich von selbst ausblendet.

### Behoben (gegenüber der Vorgängerfassung)

- Die Script-Ausgabe wurde aus einem Hintergrund-Thread direkt in die
  Oberfläche geschrieben; das konnte das Fenster einfrieren lassen.
- Die Fehlerausgabe wurde erst nach der normalen Ausgabe gelesen. Bei viel
  Fehlerausgabe blieb das Script dadurch hängen.
- Umlaute in der Ausgabe konnten das Mitlesen abbrechen.
- Scripts liefen im Ordner des Managers statt in ihrem eigenen.
- Installationen froren die Oberfläche bis zu zwei Minuten ein.
- Die Abhängigkeitsprüfung meldete Standardmodule, lokale Module und Module
  mit abweichendem Paketnamen fälschlich als fehlend.
- Ein Zeitplan ließ sich nicht mehr beenden.
- Die Suche brachte die Reihenfolge der Modulliste durcheinander.
