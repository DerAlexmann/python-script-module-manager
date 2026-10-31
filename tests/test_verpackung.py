"""Vorkehrungen für die Auslieferung, die sich sonst erst im Release zeigen.

Die meisten Tests lesen Workflows und Begleitdateien, weil ein Fehler dort beim
Entwickeln nie auffällt. Kommentare werden vorher entfernt: Ein erwähnender
Kommentar ist kein Beleg. PyInstaller ist fürs Testen nicht nötig; in der CI
macht BAU_PFLICHT die Tests damit zur Pflicht, denn übersprungen ist nicht grün.
"""

from __future__ import annotations

import importlib.util
import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

WURZEL = Path(__file__).resolve().parent.parent
RELEASE = WURZEL / ".github" / "workflows" / "release.yml"
CI = WURZEL / ".github" / "workflows" / "ci.yml"
DEPENDABOT = WURZEL / ".github" / "dependabot.yml"
LIZENZEN = WURZEL / "DRITTANBIETER-LIZENZEN.md"
BAUVERSIONEN = WURZEL / "requirements-build.txt"

# Was laut Prüfung der EXE von 2.0.2 im Bündel liegt, mit einem Merkmal der Lizenz.
KOMPONENTEN = [
    ("Python", "PSF License"),
    ("Tcl/Tk", "BSD"),
    ("OpenSSL", "Apache-2.0"),
    ("libffi", "MIT"),
    ("zlib", "zlib"),
    ("bzip2", "bzip2-1.0.6"),
    ("liblzma", "0BSD"),
    ("libmpdec", "BSD-2-Clause"),
    ("PyInstaller", "GPLv2"),
    ("Microsoft", "Microsoft Distributable Code"),
]


def bau_pflicht():
    return bool(os.environ.get("BAU_PFLICHT"))


def lade_skript(name):
    spec = importlib.util.spec_from_file_location(name, WURZEL / f"{name}.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


@pytest.fixture(scope="module")
def versionsinfo():
    return lade_skript("versionsinfo_erzeugen")


@pytest.fixture(scope="module")
def anfuegen():
    return lade_skript("lizenzen_anfuegen")


def ohne_kommentare(datei):
    return re.sub(r"(?mi)^\s*(#|REM\b|::).*$", "", datei.read_text(encoding="utf-8"))


def jobbloecke(datei):
    """Einen Workflow in seine Jobs zerlegen: Name -> Textblock.

    Gelesen wird erst ab "jobs:", denn "push" und "workflow_dispatch" unter
    "on:" sind genauso eingerückt und sind keine Jobs.
    """
    _, stichwort, jobs = ohne_kommentare(datei).partition("\njobs:\n")
    assert stichwort, f"In {datei.name} fehlt der Abschnitt jobs:."
    stellen = [(treffer.group(1), treffer.start())
               for treffer in re.finditer(r"^  ([\w-]+):$", jobs, re.MULTILINE)]
    bloecke = {}
    for nummer, (name, anfang) in enumerate(stellen):
        ende = stellen[nummer + 1][1] if nummer + 1 < len(stellen) else len(jobs)
        bloecke[name] = jobs[anfang:ende]
    return bloecke


def tabellenzeilen(name, sprache):
    deutsch, trenner, englisch = LIZENZEN.read_text(encoding="utf-8").partition(
        "\n# Licenses of third-party components\n")
    assert trenner, "Der englische Teil der Lizenzdatei fehlt."
    text = deutsch if sprache == "de" else englisch
    return re.findall(rf"^\|\s*\*\*{re.escape(name)}\b.*$", text, re.MULTILINE)


# --- Lizenzen ---------------------------------------------------------------

@pytest.mark.parametrize("sprache", ["de", "en"])
@pytest.mark.parametrize(("name", "merkmal"), KOMPONENTEN)
def test_jede_komponente_steht_mit_lizenz_und_link_in_der_tabelle(name, merkmal, sprache):
    # Geprüft wird die Tabellenzeile: Der blosse Name steckt auch in Links.
    zeilen = [zeile for zeile in tabellenzeilen(name, sprache)
              if merkmal in zeile and "](https://" in zeile]
    assert len(zeilen) == 1, f"{name} ({sprache}): {len(zeilen)} passende Zeilen."


def test_lizenzdatei_nennt_die_python_fassung_des_baus():
    fassung = re.search(r'python-version: "([\d.]+)"', ohne_kommentare(RELEASE)).group(1)
    for sprache in ("de", "en"):
        assert tabellenzeilen(f"Python {fassung}", sprache), (
            f"Der Release baut mit Python {fassung}, die Lizenzdatei nennt eine andere Fassung.")


def test_lizenzhinweise_erreichen_den_anwender():
    jobs = jobbloecke(RELEASE)
    assert re.search(r"^\s*cp .*DRITTANBIETER-LIZENZEN\.md.*NOTICE|"
                     r"^\s*cp .*NOTICE.*DRITTANBIETER-LIZENZEN\.md",
                     jobs["quellpaket"], re.MULTILINE), "Sie fehlen im Quellpaket."
    assert "python lizenzen_anfuegen.py" in jobs["windows-exe"], (
        "Die langen Lizenztexte werden nicht angehängt.")
    assert "dist/DRITTANBIETER-LIZENZEN.md" in jobs["windows-exe"], (
        "Die Hinweise werden nicht mit der EXE hochgeladen.")
    assert "artefakte/windows-exe/DRITTANBIETER-LIZENZEN.md" in jobs["release"], (
        "Die Hinweise hängen nicht am Release.")


@pytest.mark.parametrize("datei", ["NOTICE", "README.md", "README.en.md", "CONTRIBUTING.md"])
def test_begleitdateien_verweisen_auf_die_lizenzhinweise(datei):
    assert "DRITTANBIETER-LIZENZEN.md" in (WURZEL / datei).read_text(encoding="utf-8")


def test_lizenztexte_werden_in_der_richtigen_reihenfolge_angefuegt(anfuegen):
    text = anfuegen.zusammenstellen("Grundtext\n", "Python-Text", "PyInstaller-Text")
    assert text.index("Grundtext") < text.index("Python-Text") < text.index("PyInstaller-Text")
    assert "## Python\n\n````text\nPython-Text\n````" in text
    assert "## PyInstaller\n\n````text\nPyInstaller-Text\n````" in text


def test_lizenzdatei_landet_dort_wo_der_release_sie_sucht(anfuegen, tmp_path, monkeypatch):
    python_text = tmp_path / "python.txt"
    python_text.write_text(anfuegen.KENNUNG_PYTHON, encoding="utf-8")
    pyinstaller_text = tmp_path / "pyinstaller.txt"
    pyinstaller_text.write_text(anfuegen.KENNUNG_PYINSTALLER, encoding="utf-8")
    assert anfuegen.ZIEL.relative_to(WURZEL).as_posix() == "dist/DRITTANBIETER-LIZENZEN.md"

    ziel = tmp_path / "dist" / "DRITTANBIETER-LIZENZEN.md"
    monkeypatch.setattr(anfuegen, "ZIEL", ziel)
    monkeypatch.setattr(anfuegen, "python_lizenz", lambda: python_text)
    monkeypatch.setattr(anfuegen, "pyinstaller_lizenz", lambda: pyinstaller_text)
    anfuegen.main()

    text = ziel.read_bytes().decode("utf-8")
    assert anfuegen.KENNUNG_PYTHON in text and anfuegen.KENNUNG_PYINSTALLER in text
    assert "# Lizenzen der Fremdkomponenten" in text
    assert "\r" not in text


@pytest.mark.parametrize("dateien", [None, [], ["COPYING.txt", "COPYING.txt"]],
                         ids=["keine-angaben", "kein-treffer", "zwei-treffer"])
def test_unklarer_pyinstaller_text_bricht_ab(anfuegen, monkeypatch, dateien):
    eintraege = dateien and [SimpleNamespace(name=name) for name in dateien]
    monkeypatch.setattr(anfuegen.metadata, "files", lambda _paket: eintraege)
    with pytest.raises(SystemExit, match="COPYING.txt"):
        anfuegen.pyinstaller_lizenz()


def test_fehlendes_pyinstaller_bricht_ab(anfuegen, monkeypatch):
    def fehlt(_paket):
        raise anfuegen.metadata.PackageNotFoundError
    monkeypatch.setattr(anfuegen.metadata, "files", fehlt)
    with pytest.raises(SystemExit, match="nicht installiert"):
        anfuegen.pyinstaller_lizenz()


def test_fehlender_lizenztext_bricht_ab(anfuegen, tmp_path):
    with pytest.raises(SystemExit, match="fehlt"):
        anfuegen.lizenztext(tmp_path / "gibt-es-nicht.txt", "x")


def test_falscher_lizenztext_bricht_ab(anfuegen, tmp_path):
    datei = tmp_path / "LICENSE.txt"
    datei.write_text("etwas anderes", encoding="utf-8")
    with pytest.raises(SystemExit, match="Kennung"):
        anfuegen.lizenztext(datei, anfuegen.KENNUNG_PYTHON)


def test_echte_lizenztexte_lassen_sich_lesen(anfuegen):
    # Auf Linux liegt kein LICENSE.txt im Python-Ordner, dort zählt die CI-Pflicht.
    if not bau_pflicht() and not (sys.platform == "win32"
                                  and importlib.util.find_spec("PyInstaller")):
        pytest.skip("braucht Windows-Python und PyInstaller")
    assert anfuegen.KENNUNG_PYTHON in anfuegen.lizenztext(
        anfuegen.python_lizenz(), anfuegen.KENNUNG_PYTHON)
    assert anfuegen.KENNUNG_PYINSTALLER in anfuegen.lizenztext(
        anfuegen.pyinstaller_lizenz(), anfuegen.KENNUNG_PYINSTALLER)


# --- Versionsangaben --------------------------------------------------------

def test_versionsdatei_nutzt_die_angaben_des_programms(pm, versionsinfo):
    assert versionsinfo.aus_quelltext("VERSION") == pm.VERSION
    assert versionsinfo.aus_quelltext("PROGRAMM") == pm.PROGRAMM
    text = versionsinfo.inhalt(pm.PROGRAMM, pm.VERSION)
    assert f"StringStruct('ProductVersion', '{pm.VERSION}')" in text
    assert f"StringStruct('ProductName', {pm.PROGRAMM!r})" in text
    assert "Claude AI" in text


def test_pyproject_nennt_dieselbe_version(pm):
    text = (WURZEL / "pyproject.toml").read_text(encoding="utf-8")
    assert re.findall(r'^version = "(.+)"$', text, re.MULTILINE) == [pm.VERSION]


def test_security_nennt_die_aktuelle_reihe(pm):
    reihe = ".".join(pm.VERSION.split(".")[:2]) + ".x"
    assert f"| {reihe} | ja |" in (WURZEL / "SECURITY.md").read_text(encoding="utf-8")


def test_downloadname_passt_zum_release(versionsinfo):
    text = ohne_kommentare(RELEASE)
    assert f'ASSET: "{versionsinfo.DOWNLOADNAME}"' in text


def test_versionsdatei_wird_von_pyinstaller_angenommen(tmp_path, pm, versionsinfo):
    if bau_pflicht():
        from PyInstaller.utils.win32 import versioninfo
    else:
        versioninfo = pytest.importorskip("PyInstaller.utils.win32.versioninfo")
    datei = tmp_path / "versionsinfo.txt"
    datei.write_text(versionsinfo.inhalt(pm.PROGRAMM, pm.VERSION), encoding="utf-8")

    info = versioninfo.load_version_info_from_text_file(str(datei))
    felder = {eintrag.name: eintrag.val for eintrag in info.kids[0].kids[0].kids}
    assert felder["ProductName"] == pm.PROGRAMM
    assert felder["ProductVersion"] == pm.VERSION
    assert felder["OriginalFilename"] == versionsinfo.DOWNLOADNAME


@pytest.mark.parametrize(("version", "erwartet"), [
    ("2.0.3", (2, 0, 3, 0)),
    ("2.10", (2, 10, 0, 0)),
    ("1", (1, 0, 0, 0)),
    ("1.1.0.4", (1, 1, 0, 4)),
])
def test_vierstellig_rechnet_richtig(versionsinfo, version, erwartet):
    assert versionsinfo.vierstellig(version) == erwartet


@pytest.mark.parametrize("version", ["1.2.0rc1", "v1.2.0", "", "1..0", "1.2.3.4.5", "1.70000.0"])
def test_vierstellig_lehnt_unbrauchbares_ab(versionsinfo, version):
    with pytest.raises(SystemExit, match="VERSION"):
        versionsinfo.vierstellig(version)


@pytest.mark.parametrize("datei", ["build.cmd", ".github/workflows/release.yml"])
def test_beide_bauwege_nutzen_die_versionsdatei(datei):
    text = ohne_kommentare(WURZEL / datei)
    assert re.search(r'--version-file "?versionsinfo\.txt"?', text)
    erzeugen = text.find("versionsinfo_erzeugen.py")
    assert 0 <= erzeugen < text.lower().index("pyinstaller --noconfirm"), (
        "Die Versionsdatei muss vor dem Packen entstehen.")


def test_erzeugte_versionsdatei_ist_ignoriert():
    zeilen = (WURZEL / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "versionsinfo.txt" in zeilen


def test_release_prueft_die_fertige_exe():
    schritte = jobbloecke(RELEASE)["windows-exe"]
    assert "VersionInfo" in schritte, "Die fertige EXE wird nicht angesehen."
    assert re.search(r'GITHUB_REF_TYPE -eq \'tag\' -and "v\$\(\$info\.ProductVersion\)" '
                     r"-ne \$env:GITHUB_REF_NAME", schritte), (
        "Eine vergessene Versionsanhebung fiele beim Taggen nicht auf.")


# --- Fester Bau --------------------------------------------------------------

def test_bauversionen_sind_festgelegt():
    zeilen = [zeile.split("#")[0].strip()
              for zeile in BAUVERSIONEN.read_text(encoding="utf-8").splitlines()]
    pakete = [zeile for zeile in zeilen if zeile]
    assert any(zeile.lower().startswith("pyinstaller") for zeile in pakete)
    for zeile in pakete:
        assert re.fullmatch(r"[\w.\-]+==\d+(\.\d+)*", zeile), f"nicht festgelegt: {zeile}"


def test_release_baut_aus_den_festen_versionen():
    zeilen = [zeile for zeile in ohne_kommentare(RELEASE).splitlines() if "pip install" in zeile]
    assert any("-r requirements-build.txt" in zeile for zeile in zeilen)
    assert not [zeile for zeile in zeilen if re.search(r"pip install\s+pyinstaller", zeile)]


def test_ci_prueft_die_festen_versionen_als_pflicht():
    jobs = jobbloecke(CI)
    job = next((text for text in jobs.values() if "-r requirements-build.txt" in text), "")
    assert job, "Kein CI-Job installiert die festen Bauversionen."
    assert "windows-latest" in job
    assert re.search(r'BAU_PFLICHT:\s*"1"', job), "Ohne Pflicht wäre ein Überspringen grün."
    assert "tests/test_verpackung.py" in job


def test_dependabot_laesst_untergrenzen_in_ruhe():
    bloecke = re.split(r"(?m)^  - package-ecosystem:", ohne_kommentare(DEPENDABOT))[1:]
    pip = [block for block in bloecke if block.strip().startswith('"pip"')]
    assert len(pip) == 1
    assert re.search(r'^\s*versioning-strategy:\s*"?increase-if-necessary"?\s*$',
                     pip[0], re.MULTILINE)
    assert any(block.strip().startswith('"github-actions"') for block in bloecke)


# --- Release-Workflow --------------------------------------------------------

def test_nur_der_release_job_haengt_am_tag():
    jobs = jobbloecke(RELEASE)
    bedingung = re.search(r"^    if:(.*)$", jobs["release"], re.MULTILINE)
    assert bedingung, "Ohne Tag bräche ein Probelauf an diesem Job ab."
    # Der genaue Ausdruck: Ein verdrehtes "!=" enthielte dasselbe Stichwort.
    assert re.fullmatch(r"""\s*github\.ref_type == 'tag'\s*""", bedingung.group(1))
    for name in ("quellpaket", "windows-exe"):
        assert not re.search(r"^    if:", jobs[name], re.MULTILINE), (
            f"{name} würde beim Probelauf nicht mehr gebaut.")


def test_release_bleibt_ein_entwurf():
    assert re.search(r"^\s*draft: true", jobbloecke(RELEASE)["release"], re.MULTILINE)


def test_fehlende_dateien_lassen_den_release_scheitern():
    text = ohne_kommentare(RELEASE)
    hochladen = len(re.findall(r"actions/upload-artifact@", text))
    assert hochladen and len(re.findall(r"if-no-files-found: error", text)) == hochladen
    assert re.search(r"fail_on_unmatched_files: true", text)


def test_zipname_vertraegt_schraegstriche_im_ref():
    assert "${GITHUB_REF_NAME//\\//-}" in jobbloecke(RELEASE)["quellpaket"]


def test_rauchtest_verlangt_das_programmfenster():
    # Dass der Prozess lebt, beweist wenig: Auch ein Fehlerfenster hält ihn am Leben.
    schritte = jobbloecke(RELEASE)["windows-exe"]
    assert "MainWindowTitle -eq $env:NAME" in schritte
