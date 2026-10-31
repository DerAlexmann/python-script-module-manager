# Lizenzen der Fremdkomponenten

Der Quellcode des Python-Script & Module Managers steht unter der MIT-Lizenz – siehe
[LICENSE](LICENSE). Diese Datei listet die Bestandteile anderer Projekte auf, die in der
fertigen **Windows-EXE** mitgeliefert werden.

*English version below – [Licenses of third-party components](#licenses-of-third-party-components).*

## Das Wichtigste

- **Das Skript** liefert nichts mit und braucht nur die Standardbibliothek von Python.
- **Die EXE bleibt als Gesamtwerk MIT.** Sie enthält keine Komponente, deren Lizenz das
  ganze Programm erfassen würde.
- **Der Bootloader von PyInstaller** steht zwar unter der GPL, die Lizenz erlaubt aber
  ausdrücklich, ihn ohne Einschränkung in andere Programme einzubetten.
- Die Fassung dieser Datei, die jedem Release beiliegt, enthält am Ende die vollständigen
  Lizenztexte von Python und PyInstaller, entnommen aus den Fassungen des jeweiligen Baus.

## Was in der Windows-EXE steckt

| Bestandteil | Lizenz | Lizenztext und Quellcode |
|---|---|---|
| **Python 3.12** – Laufzeit und Standardbibliothek | PSF License 2.0 | [docs.python.org](https://docs.python.org/3.12/license.html), [Quellcode](https://github.com/python/cpython/tree/3.12) |
| **Tcl/Tk 8.6** – die Oberfläche (`tcl86t.dll`, `tk86t.dll`) | Tcl/Tk-Lizenz (BSD-artig) | [tcl-lang.org](https://www.tcl-lang.org/software/tcltk/license.html) |
| **OpenSSL 3** (`libcrypto-3.dll`) | Apache-2.0 | [LICENSE.txt](https://github.com/openssl/openssl/blob/master/LICENSE.txt) |
| **libffi** (`libffi-8.dll`) | MIT | [LICENSE](https://github.com/libffi/libffi/blob/master/LICENSE) |
| **zlib** (`zlib1.dll`) | zlib-Lizenz | [zlib.net](https://zlib.net/zlib_license.html) |
| **bzip2** – in `_bz2.pyd` | bzip2-1.0.6-Lizenz (BSD-artig) | [sourceware.org](https://sourceware.org/bzip2/) |
| **liblzma** (XZ Utils) – in `_lzma.pyd` | Public Domain oder 0BSD, je nach Fassung | [tukaani.org](https://tukaani.org/xz/) |
| **libmpdec** – in `_decimal.pyd` | BSD-2-Clause | [bytereef.org](https://www.bytereef.org/mpdecimal/) |
| **PyInstaller** – der Bootloader startet die gepackte Anwendung | GPLv2 oder neuer **mit** Bootloader-Ausnahme; Laufzeit-Hooks Apache-2.0 | [Lizenzhinweis](https://pyinstaller.org/en/stable/license.html), [COPYING.txt](https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt) |
| **Microsoft C-Laufzeit** (`VCRUNTIME140.dll`, `ucrtbase.dll`, `api-ms-win-*.dll`) | Microsoft Distributable Code | [Weitergabe](https://learn.microsoft.com/en-us/cpp/windows/determining-which-dlls-to-redistribute), [Universal CRT](https://learn.microsoft.com/en-us/cpp/windows/universal-crt-deployment), [Lizenzbedingungen](https://visualstudio.microsoft.com/license-terms/) |

Der Quellcode dieses Programms liegt zu jeder Version als ZIP am [Release](../../releases)
und im Verlauf dieses Repositorys.

### Microsoft-Komponenten

Die C-Laufzeit gehört nicht zu diesem Projekt und liegt trotzdem in der EXE, sie ist also
keine bloße Systembibliothek. Sie darf weitergegeben werden, solange Urheberrechts-,
Marken- und Patenthinweise unverändert bleiben, Microsofts Marken nicht den Eindruck einer
Herkunft von oder Billigung durch Microsoft erwecken, sie nur auf Microsoft-Plattformen
läuft und nicht Teil schädlicher, irreführender oder rechtswidriger Programme ist. Die
genauen Bedingungen stehen im Abschnitt „Additional Conditions for this Windows binary
build" des Python-Lizenztexts und bei Microsoft.

Andere Windows-Bibliotheken wie `KERNEL32.dll` oder `USER32.dll` gehören zum Betriebssystem
und sind nicht Teil der EXE.

## Pflege dieser Datei

Ändert sich der Inhalt der EXE, gehört das hier hinein. Nachsehen lässt er sich ohne
Start: `grep -a -o -E '[A-Za-z0-9_.+-]+\.(dll|pyd)' Python-Script-Module-Manager.exe | sort -u`.
Der Test `tests/test_verpackung.py` prüft, dass die Tabellen vollständig sind und die Datei
dem Release beiliegt.

## Kurze Lizenztexte / Short license texts

### zlib

```text
Copyright (C) 1995-2011 Jean-loup Gailly and Mark Adler

This software is provided 'as-is', without any express or implied
warranty.  In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.

2. Altered source versions must be plainly marked as such, and must not be
   misrepresented as being the original software.

3. This notice may not be removed or altered from any source distribution.

Jean-loup Gailly        Mark Adler
jloup@gzip.org          madler@alumni.caltech.edu
```

### libmpdec

```text
Copyright (c) 2008-2020 Stefan Krah. All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.
```

---

# Licenses of third-party components

The source code of Python-Script & Module Manager is licensed under the MIT License – see
[LICENSE](LICENSE). This file lists the components from other projects that ship inside
the finished **Windows executable**.

## The short version

- **The script** bundles nothing and only needs Python's standard library.
- **The executable as a whole remains MIT.** It contains no component whose license would
  extend to the whole program.
- **The PyInstaller bootloader** is under the GPL, but its license expressly allows
  embedding it in other programs without restriction.
- The copy of this file attached to each release ends with the full license texts of
  Python and PyInstaller, taken from the versions used for that build.

## What is inside the Windows executable

| Component | License | License text and source |
|---|---|---|
| **Python 3.12** – runtime and standard library | PSF License 2.0 | [docs.python.org](https://docs.python.org/3.12/license.html), [source](https://github.com/python/cpython/tree/3.12) |
| **Tcl/Tk 8.6** – the user interface (`tcl86t.dll`, `tk86t.dll`) | Tcl/Tk license (BSD-style) | [tcl-lang.org](https://www.tcl-lang.org/software/tcltk/license.html) |
| **OpenSSL 3** (`libcrypto-3.dll`) | Apache-2.0 | [LICENSE.txt](https://github.com/openssl/openssl/blob/master/LICENSE.txt) |
| **libffi** (`libffi-8.dll`) | MIT | [LICENSE](https://github.com/libffi/libffi/blob/master/LICENSE) |
| **zlib** (`zlib1.dll`) | zlib license | [zlib.net](https://zlib.net/zlib_license.html) |
| **bzip2** – inside `_bz2.pyd` | bzip2-1.0.6 license (BSD-style) | [sourceware.org](https://sourceware.org/bzip2/) |
| **liblzma** (XZ Utils) – inside `_lzma.pyd` | public domain or 0BSD, depending on the version | [tukaani.org](https://tukaani.org/xz/) |
| **libmpdec** – inside `_decimal.pyd` | BSD-2-Clause | [bytereef.org](https://www.bytereef.org/mpdecimal/) |
| **PyInstaller** – its bootloader starts the packaged application | GPLv2 or later **with** the bootloader exception; run-time hooks Apache-2.0 | [license notice](https://pyinstaller.org/en/stable/license.html), [COPYING.txt](https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt) |
| **Microsoft C runtime** (`VCRUNTIME140.dll`, `ucrtbase.dll`, `api-ms-win-*.dll`) | Microsoft Distributable Code | [redistribution](https://learn.microsoft.com/en-us/cpp/windows/determining-which-dlls-to-redistribute), [Universal CRT](https://learn.microsoft.com/en-us/cpp/windows/universal-crt-deployment), [license terms](https://visualstudio.microsoft.com/license-terms/) |

The source code of this program is attached to every [release](../../releases) as a ZIP
file and is part of this repository's history.

### Microsoft components

The C runtime is not part of this project but does sit inside the executable, so it is not
merely a system library. It may be redistributed as long as copyright, trademark and patent
notices stay unaltered, Microsoft's trademarks do not suggest that the program comes from
or is endorsed by Microsoft, it runs only on Microsoft platforms, and it is not part of a
malicious, deceptive or unlawful program. The exact terms are in the section "Additional
Conditions for this Windows binary build" of the Python license text and at Microsoft.

Other Windows libraries such as `KERNEL32.dll` or `USER32.dll` belong to the operating
system and are not part of the executable.

## Keeping this file current

When the contents of the executable change, that belongs in here. They can be listed
without starting it: `grep -a -o -E '[A-Za-z0-9_.+-]+\.(dll|pyd)' Python-Script-Module-Manager.exe | sort -u`.
The test `tests/test_verpackung.py` checks that the tables are complete and that the file
ships with the release.
