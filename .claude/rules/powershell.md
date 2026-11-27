---
paths:
  - "**/*.ps1"
  - "**/*.ps1.j2"
---

# PowerShell — always apply

The `mh` launcher (`src/media_hygiene/cli/templates/mh*.ps1.j2`, rendered by `launcher`) and
the measurement harness (`tests/measure/mh-measure.ps1`) run on **Windows PowerShell 5.1**,
the one Windows ships; PowerShell 7 is not installed on the maintainer's PC and is not a
target. No PowerShell runs in the devcontainer: nothing here executes what you write.

- ✅ DO: 5.1 syntax only: no `&&` / `||` between commands, no `??`, no ternary, no
  `-ExecutionPolicy Bypass` anywhere. ❌ DON'T: ask for a check "in PowerShell 7".
- ✅ DO: pure ASCII in every rendered `.ps1` (`tests/unit/test_launcher_ascii.py`,
  `test_measure_script.py`): PowerShell rebuilds the accented folder names itself; a file
  written through `>` survives any code page. Messages to a French user stay ASCII too
  (`Noel`, not `Noël`) unless built at run time.
- ✅ DO: `Shell.Application` only for the phone and the folder picker (`CopyHere`, never
  `MoveHere`, `InvokeVerb` or `.Delete(`); ❌ DON'T: `Add-Type`, `System.Windows.Forms`, a
  kernel32 `DllImport`, a child `conhost.exe` with `Bypass`: Avast's Behavior Shield quarantines
  them (measured 2026-10-16), then refuses any new file at that path until a reboot.
- ✅ DO: `robocopy` without `/PURGE` or `/MIR` (`test_launcher_push.py`): a deletion by mistake
  is never propagated. A refusal is comments to read on screen, then one `throw` 5.1 cannot
  garble (`test_launcher_refusal.py`).
- ✅ DO: `mkdir -Force` (and the like) in every documented command: without it 5.1 prints a red
  error when the folder exists (`tests/unit/test_documentation.py`).
- ❌ DON'T: name a variable like a parameter in another case (`$photos` vs `-Photos`):
  PowerShell names ignore case, and a typed parameter (`[string]`) silently converts what is
  assigned (a list of files became one string, 2026-10-20).
- ✅ DO: files the user may have edited in Notepad or written by 5.1 carry a UTF-8 BOM: read
  them through `text_files.py`, never `read_text("utf-8")`.
- ✅ DO: `mh-measure.ps1` writes its results to `%TEMP%\mh-measure-results` and works in
  `%TEMP%\mh-measure`; `$HOME\media-hygiene` is for what `mh` itself keeps, nothing temporary.
  A measurement only the maintainer can run becomes a numbered step of that script, never a
  list of commands to type; its results file is read back from the devcontainer through a
  read-only mount of `C:\`.
- ✅ DO: before handing over a `.ps1`, parse it with the PowerShell container (no `pwsh` here):
  `docker run --rm -i mcr.microsoft.com/powershell:lts-7.4-alpine-3.20 pwsh -NoProfile -Command
  '$t=[Console]::In.ReadToEnd(); $e=$null;
  $null=[System.Management.Automation.Language.Parser]::ParseInput($t,[ref]$null,[ref]$e);
  if ($e.Count) { $e | % { "{0}: {1}" -f $_.Extent.StartLineNumber, $_.Message } } else { "parse OK" }'
  < tests/measure/mh-measure.ps1` (a merge once lost a brace: the run failed at once, 2026-11-11).
- ✅ DO: give the fetch **and** run lines, with the commit SHA in the raw URL (a branch URL is
  cached 5 minutes by raw.githubusercontent.com): `Invoke-WebRequest
  https://raw.githubusercontent.com/<owner>/<repo>/<sha>/tests/measure/mh-measure.ps1 -OutFile
  .\mh-measure.ps1`, `Unblock-File .\mh-measure.ps1`, `.\mh-measure.ps1 -Only N`. ❌ DON'T: the
  bare script name (it lives in the repository, not on the PC).
