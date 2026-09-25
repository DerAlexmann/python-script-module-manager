# Sicherheit

## Eine Lücke melden

Bitte **kein öffentliches Issue** für Sicherheitslücken. Melde sie über
GitHub: Reiter **Security** → **Report a vulnerability**
([private Sicherheitsmeldung](../../security/advisories/new)). Die Meldung ist
nur für die Projektbetreuung sichtbar.

Hilfreich sind: eine Beschreibung des Problems, die Version des Programms (sie
steht in der Kopfzeile und auf dem Reiter „Info & Copyright"), das
Betriebssystem und, wenn möglich, eine Anleitung zum Nachstellen.

Eine Antwort kommt in der Regel innerhalb einer Woche.

## Unterstützte Versionen

Gepflegt wird jeweils die neueste veröffentlichte Version.

| Version | Unterstützt |
|---|---|
| 2.0.x | ja |
| älter | nein |

## Was das Programm tut – und was nicht

- **Scripts laufen mit deinen Rechten.** Der Manager startet die Scripts, die
  du in die Liste aufgenommen hast, mit der gewählten Python-Installation und
  denselben Rechten wie das Programm selbst. Nimm nur Scripts auf, denen du
  vertraust. Ein Zeitplan startet ein Script ohne weitere Rückfrage.
- **Die Abhängigkeitsprüfung führt nichts aus.** Die Importe werden aus dem
  Quelltext gelesen (`ast`), das Script wird dafür nicht gestartet. Auch
  beim Einlesen der Module wird kein Paket importiert; gelesen werden nur die
  Paketdaten der Installation.
- **pip lädt aus dem Internet.** Installieren und Aktualisieren rufen
  `python -m pip install …` auf; pip bezieht die Pakete aus dem Python Package
  Index oder aus den Quellen, die in deiner pip-Konfiguration stehen.
  Paketnamen, die der Manager vorschlägt, sind Vermutungen aus dem Importnamen.
  Prüfe vor dem Installieren, ob das Paket wirklich das gemeinte ist –
  Tippfehler-Pakete gibt es.
- **Keine Administratorrechte.** Der Manager fordert keine erhöhten Rechte an.
  Liegt eine Installation in einem geschützten Ordner, meldet pip das im
  Protokoll.
- **Deinstallieren nur nach Rückfrage.** Jede Deinstallation – über Schalter,
  Rechtsklick, Entf-Taste oder das Info-Fenster – fragt vorher nach.
- **Sonst keine Verbindungen.** Außer über pip baut das Programm keine
  Netzwerkverbindungen auf und lädt nichts nach.
- **Gespeichert** werden in `python-script-module-manager.json` neben dem
  Programm: Pfade und Namen der Scripts, Pfade der Python-Installationen,
  deren Modullisten, Sprache, Schema und Fensterlage. Wer die Datei
  weitergibt, gibt diese Pfade mit weiter.

## Die veröffentlichte EXE

Die EXE ist nicht signiert. Prüfe nach dem Herunterladen die SHA-256-Summe
gegen die Angabe in den Release-Notizen:

```powershell
Get-FileHash .\Python-Script-Module-Manager.exe -Algorithm SHA256
```

Wer lieber nichts Fertiges ausführt: Das Programm ist eine einzige lesbare
Python-Datei und lässt sich mit `build.cmd` selbst bauen.
