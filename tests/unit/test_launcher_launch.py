"""How the shortcut and the right-click entry start `mh`; older ones refreshed.

TODO 0257: Avast stopped `powershell.exe -ExecutionPolicy Bypass` started by the
right-click (IDP.HELU.PSD11, 2026-10-19); an antivirus exception is no answer. The
start loads `mh.ps1` under the user's own policy (RemoteSigned, step 1 of the guides),
says the line to type when it is refused, and a start written before is rewritten when
`mh.ps1` is loaded. No PowerShell here: the rendered text is checked, as PowerShell
would read it.
"""

from __future__ import annotations

import re
from typing import Final

import pytest

from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.paths.docker_run import Shell
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_host import EXPLORER_KEY, FROM_EXPLORER
from media_hygiene.services.launcher_launch import FLAGGED, POLICY_LINE, launch_texts
from tests.unit.test_launcher_ascii import accented_runtime, expanded

COMMANDS: Final = LauncherCommands(
    names=("audit", "home", "menu"),
    writers=(),
    pages=("home",),
    data=("menu",),
    port=8088,
)
# The keep-awake of long commands (0179): measured with no alert in a user-like run
# (2026-10-16), kept by the maintainer; the one compiled call of the script.
_KEEP_AWAKE: Final = "Add-Type -Namespace MediaHygiene -Name Power"


def _script(locale: Locale, shell: Shell | None = None) -> str:
    """The rendered `mh`, in that language."""
    with using(locale):
        return render_script(launcher_script(accented_runtime(), shell, COMMANDS))


def _body(text: str, name: str) -> str:
    """One function of the script, up to its closing brace."""
    body = text[text.index(f"function global:_mh_{name}") :]
    return body[: body.index("\n}\n")]


@pytest.mark.parametrize("locale", [Locale.EN, Locale.FR])
def test_no_rendered_launcher_holds_what_antivirus_heuristics_flag(
    locale: Locale,
) -> None:
    """No bypass, encoded command, Invoke-Expression, hidden window nor conhost."""
    for shell in (None, Shell.BASH):
        text = _script(locale, shell)
        assert shell is Shell.BASH or text.isascii()
        # " -ExecutionPolicy": the option (Set-ExecutionPolicy, the line said, is fine).
        for flagged in (*FLAGGED, " -ExecutionPolicy", "iex ", "Start-Process conhost"):
            assert flagged.lower() not in text.lower(), flagged
    powershell = _script(locale)
    code = [
        line for line in powershell.splitlines() if not line.lstrip().startswith("#")
    ]
    assert [line.strip() for line in code if "Add-Type" in line] == [
        line.strip() for line in code if _KEEP_AWAKE in line
    ]
    assert powershell.count(_KEEP_AWAKE) == 1
    assert "Add-Type" not in _body(powershell, "start(")


def test_the_start_loads_the_file_under_the_users_own_policy() -> None:
    """`-NoExit -Command`, the file loaded in a try, the words last (Explorer's `#`)."""
    start = _body(_script(Locale.EN), "start(")
    assert "'-NoExit -Command \"' + $load + '; ' + $words + '\"'" in start
    assert (
        '$load = "try { . \'" + $file.Replace("\'", "\'\'") + "\' } catch { '
        "function global:mh { Write-Host 'PowerShell refused to load mh.ps1. Type "
        f"this line once, then start Media Hygiene again: {POLICY_LINE}' }} }}\""
    ) in start


def test_a_refused_policy_says_the_line_in_french_too() -> None:
    """The line said by the stub `mh`, translated; its quotes safe in single quotes."""
    start = expanded(_body(_script(Locale.FR), "start("))
    assert "PowerShell a refusé de charger mh.ps1. Tapez une fois cette ligne" in start
    assert f"{POLICY_LINE}' }} }}\"" in start
    with using(Locale.FR):
        policy = launch_texts().policy
    assert '"' not in policy
    assert "$" not in policy
    assert re.fullmatch(r"(?:[^']|'')*", policy)


def _started(file: str, words: str) -> str:
    """What `_mh_start` gives, computed as its PowerShell line does."""
    load = (
        "try { . '" + file.replace("'", "''") + "' } catch { function global:mh "
        "{ Write-Host 'PowerShell refused' } }"
    )
    return '-NoExit -Command "' + load + "; " + words + '"'


def test_explorer_folder_still_comes_after_the_comment() -> None:
    """The try/catch comes first: `#" "%V` stays last, the folder read back."""
    arguments = _started("C:\\Users\\O'Neil\\mh.ps1", f'mh {FROM_EXPLORER} #" "%V')
    line = arguments.replace("%V", "D:\\L'été 2019")
    assert line.endswith('mh --from-explorer #" "D:\\L\'été 2019"')
    code = line[: line.rindex("#")]
    assert code.count("{") == code.count("}")  # the try/catch closed before the comment
    assert "O''Neil" in code


def test_loading_the_file_refreshes_the_older_starts_of_this_file_only() -> None:
    """At load: shortcuts and entries naming this file, another command: rewritten."""
    text = _script(Locale.EN)
    loaded = text.index("\ntry { _mh_refresh } catch { }\n")
    assert loaded > text.index("function global:_mh_said(")
    body = _body(text, "refresh {")
    assert "if ($env:OS -ne 'Windows_NT' -or -not $file) { return }" in body
    assert '$named = "\'" + $file.Replace("\'", "\'\'") + "\'"' in body
    # Only what exists, names this file and starts it otherwise.
    assert "if (-not (Test-Path -LiteralPath $path)) { continue }" in body
    assert (
        "if (-not $link.Arguments.Contains($named) -or $link.Arguments -eq $arguments)"
        " { continue }"
    ) in body
    assert (
        "if (-not $read.Contains($named) -or $read -eq $command) { continue }" in body
    )
    assert f"foreach ($key in '{EXPLORER_KEY}'" in body
    assert "New-Item -ItemType" not in body  # nothing created here
    # Each one read back, then said.
    assert body.count("_mh_said (") == 2
    assert "_mh_said ($shell.CreateShortcut($path).Arguments -eq $arguments)" in body
    assert "_mh_said ($back -and $back.GetValue('') -eq $command)" in body
    said = _body(text, "said(")
    assert (
        'Write-Host "Brought up to date, read back from ${path}: it starts this mh."'
        in said
    )
    assert "Could not write ${path}." in said


def test_the_refresh_line_is_translated() -> None:
    """The French line, its `${path}` kept."""
    said = expanded(_body(_script(Locale.FR), "said("))
    assert "${path}" in said
    assert "Brought up to date" not in said
