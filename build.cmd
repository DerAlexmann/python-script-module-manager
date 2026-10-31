@echo off
REM ---------------------------------------------------------------------
REM Baut "Python-Script & Module Manager.exe" neu; das Ergebnis liegt
REM anschliessend im Ordner dist.
REM
REM Voraussetzung:  pip install -r requirements-build.txt
REM Das Symbol entsteht bei Bedarf mit:  python icon_erzeugen.py
REM ---------------------------------------------------------------------
setlocal

REM Python finden: bevorzugt ueber den Windows-Starter py, sonst python
set "PY=py -3"
py -3 --version >nul 2>nul || set "PY=python"

%PY% versionsinfo_erzeugen.py
if errorlevel 1 (
  echo.
  echo Die Versionsangaben liessen sich nicht erzeugen.
  pause
  exit /b 1
)

%PY% -m PyInstaller --noconfirm --onefile --windowed --clean ^
  --name "Python-Script & Module Manager" ^
  --icon "script_module_manager.ico" ^
  --version-file "versionsinfo.txt" ^
  "Python-Script & Module Manager.pyw"

if errorlevel 1 (
  echo.
  echo Der Bau ist fehlgeschlagen. Fehlt PyInstaller?
  echo     pip install -r requirements-build.txt
  pause
  exit /b 1
)

echo.
echo Fertig: "dist\Python-Script & Module Manager.exe"
pause
