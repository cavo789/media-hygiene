"""`mh` and a port being released: waited for, never "close Idle" (0503).

PID 0 (Windows' System Idle Process) is what Get-NetTCPConnection names for a socket
whose owner has just exited; `mh` waits for it, a line said once, and refuses in red
only when the port is still taken; every refusal comes before any line of success.
"""

from __future__ import annotations

from typing import Final

import pytest

from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_guards import launcher_guards
from media_hygiene.services.launcher_port import (
    PORT_POLL_MILLISECONDS,
    PORT_RELEASE_SECONDS,
)
from tests.unit.test_launcher_ascii import accented_runtime, expanded

_PORT: Final = 8088
_COMMANDS: Final = LauncherCommands(
    ("audit", "review", "menu"), (), ("review",), ("menu",), _PORT
)


def _shown() -> str:
    """The rendered mh.ps1, in English, its escapes expanded."""
    with using(Locale.EN):
        text = render_script(launcher_script(accented_runtime(), None, _COMMANDS))
    assert text.isascii()
    return expanded(text)


def _body(shown: str, name: str) -> str:
    """The body of the PowerShell function `name`."""
    start = shown.index(f"function global:{name}")
    assert shown[start + len(f"function global:{name}")] in " ("
    body = shown[start:]
    return body[: body.index("\n}\n")]


def test_pid_zero_or_a_gone_process_is_no_holder() -> None:
    """PID 0, or a process that no longer exists: a socket being released."""
    holder = _body(_shown(), "_mh_port_holder")
    assert "if ($process) { Get-Process -Id $process" in holder
    assert "if (-not $found) { $releasing = $true; continue }" in holder
    assert "if ($releasing) { return @{ name = '' } }" in holder


def test_a_port_being_released_is_waited_for() -> None:
    """Polled every 500 ms up to the limit, one line said, refused in red at the end."""
    shown = _shown()
    body = _body(shown, "_mh_page_free")
    with using(Locale.EN):
        port = launcher_guards().port
    assert f"(Get-Date).AddSeconds({PORT_RELEASE_SECONDS})" in body
    assert f"Start-Sleep -Milliseconds {PORT_POLL_MILLISECONDS}" in body
    assert f'if (-not $said) {{ Write-Host "{port.releasing}"; $said = $true }}' in body
    assert f'Write-Host "{port.released}" -ForegroundColor Red; return $false' in body
    assert "$port = 8088" in body
    assert "${port}" in port.releasing
    assert "${port}" in port.released
    assert "${name}" not in port.released


@pytest.mark.parametrize("text", ["held", "open", "unshared"])
def test_refusals_are_red(text: str) -> None:
    """Every refusal of the guards in red; informational lines unchanged."""
    shown = _shown()
    with using(Locale.EN):
        texts = launcher_guards().texts
    assert f'Write-Host "{getattr(texts, text)}" -ForegroundColor Red' in shown
    assert f'Write-Host "{texts.stopped}"\n' in shown


def test_the_port_is_checked_before_any_line_of_success() -> None:
    """Home and `mh --lan`: the guard runs before the running / LAN lines."""
    shown = _shown()
    home = _body(shown, "_mh_home")
    assert home.index("_mh_page_free") < home.index("Write-Host")
    lan = _body(shown, "_mh_lan_open")
    assert lan.index("_mh_page_free") < lan.index("Write-Host")
    assert "if (-not (_mh_lan_open $true)) { return }" in _body(shown, "_mh_lan")


def test_home_loop_reopens_home_after_a_refused_step() -> None:
    """A step refused (exit 1) is under the step base: home started again."""
    home = _body(_shown(), "_mh_home")
    assert "if ($status -le 20) {" in home
    # The step's code read, then the loop's top: under the base, home again.
    assert home.rstrip().endswith("$status = $LASTEXITCODE\n    }")
