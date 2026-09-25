@echo off
REM ---------------------------------------------------------------------
REM Baut "Python-Script & Module Manager.exe" neu; das Ergebnis liegt
REM anschliessend im Ordner dist.
REM
REM Voraussetzung:  pip install pyinstaller
REM Das Symbol entsteht bei Bedarf mit:  python icon_erzeugen.py
REM ---------------------------------------------------------------------
setlocal

REM Python finden: bevorzugt ueber den Windows-Starter py, sonst python
set "PY=py -3"
py -3 --version >nul 2>nul || set "PY=python"

%PY% -m PyInstaller --noconfirm --onefile --windowed --clean ^
  --name "Python-Script & Module Manager" ^
  --icon "script_module_manager.ico" ^
  "Python-Script & Module Manager.pyw"

if errorlevel 1 (
  echo.
  echo Der Bau ist fehlgeschlagen. Fehlt PyInstaller?
  echo     pip install pyinstaller
  pause
  exit /b 1
)

echo.
echo Fertig: "dist\Python-Script & Module Manager.exe"
pause
