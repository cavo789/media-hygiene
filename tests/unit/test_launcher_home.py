"""`mh` alone: the home page; a step chosen there runs here, then the page again.

TODO 0210. `home` ends with `100 + n` for step `n` (0209) only when the launcher says
it relays the steps: `-e MEDIA_HYGIENE_LAUNCHER_STEPS=1`, set by this loop alone.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.constants import ExitCode, Locale
from media_hygiene.i18n import using
from media_hygiene.paths.docker_run import Shell
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from tests.support.host_bash import run_bash
from tests.support.runtime import make_locations, make_runtime
from tests.unit.test_launcher_ascii import accented_runtime

if TYPE_CHECKING:
    import subprocess
    from pathlib import Path

_COMMANDS: Final = LauncherCommands(
    names=("audit", "browse", "clean", "history", "home", "menu"),
    writers=("clean",),
    pages=("home", "browse"),
    data=("menu",),
    port=8088,
)
_RELAY: Final = f"{LAUNCHER_STEPS_VARIABLE}=1"
# `menu` prints its steps; `home` exits with the next code of $CODES (then 0) and
# says whether it was told to relay; any other command says it ran.
_FAKE_DOCKER: Final = r"""
docker() {
    if [[ "$1" == version ]]; then return 0; fi
    if [[ " $* " == *" menu "* ]]; then
        printf '0\taudit\n1\taudit\n2\tclean --tier near\n3\thistory\n4\tbrowse\n'
        return 0
    fi
    if [[ " $* " == *" browse "* ]]; then
        local ended=0
        if [[ -s "$HOME/browse" ]]; then read -r ended < "$HOME/browse"; fi
        if [[ " $* " == *" -e RELAY "* ]]; then
            echo "browse:relayed"
        else
            echo "browse:alone"
        fi
        return "$ended"
    fi
    if [[ " $* " == *" home "* ]]; then
        local code=0 rest
        if [[ -s "$HOME/codes" ]]; then
            read -r code rest < "$HOME/codes"
            printf '%s\n' "$rest" > "$HOME/codes"
        fi
        if [[ " $* " == *" -e RELAY "* ]]; then
            echo "home:relayed"
        else
            echo "home:alone"
        fi
        return "${code:-0}"
    fi
    for arg in "$@"; do
        if [[ "$arg" == history || "$arg" == clean ]]; then echo "ran:$arg"; fi
    done
    return 0
}
"""


def _bash(
    tmp_path: Path, line: str, codes: str | tuple[str, str]
) -> subprocess.CompletedProcess[str]:
    """Load the bash `mh` and run `line`; `home` exits with `codes`, one by one.

    A pair: `home`'s codes, then `browse`'s (its *Apply now* ends on that code).
    """
    codes, browse = codes if isinstance(codes, tuple) else (codes, "0")
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    script = tmp_path / "mh.sh"
    script.write_text(render_script(launcher_script(runtime, Shell.BASH, _COMMANDS)))
    (tmp_path / "codes").write_text(f"{codes}\n")
    (tmp_path / "browse").write_text(f"{browse}\n")
    fake = _FAKE_DOCKER.replace("RELAY", _RELAY)
    code = f"{fake}\nsource {script}; {line}; echo status=$?"
    return run_bash(code, {"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"})


def _lines(done: subprocess.CompletedProcess[str]) -> list[str]:
    """What the fake image said, in order, and the final status."""
    return [line for line in done.stdout.splitlines() if ":" in line or "=" in line]


def test_a_step_chosen_runs_then_the_page_comes_back(tmp_path: Path) -> None:
    """103: step 3 (`history`) runs, then `home` again, which ends with 0."""
    done = _bash(tmp_path, "mh", "103")
    assert _lines(done) == ["home:relayed", "ran:history", "home:relayed", "status=0"]
    assert "Next time, type it directly: mh history" in done.stderr


def test_two_steps_in_a_row(tmp_path: Path) -> None:
    """Each step chosen runs in turn; a writer gets the photos writable."""
    done = _bash(tmp_path, "mh", "102 103")
    assert _lines(done) == [
        "home:relayed",
        "ran:clean",
        "home:relayed",
        "ran:history",
        "home:relayed",
        "status=0",
    ]


@pytest.mark.parametrize(("code", "status"), [("0", 0), ("1", 1), ("125", 125)])
def test_quit_or_an_error_ends_the_loop_with_its_code(
    tmp_path: Path, code: str, status: int
) -> None:
    """0 (Quit, Ctrl+C), an error, a code naming no step: no step runs."""
    done = _bash(tmp_path, "mh", code)
    assert _lines(done) == ["home:relayed", f"status={status}"]


def test_browse_from_home_runs_the_step_its_apply_now_chose(tmp_path: Path) -> None:
    """0243: browse opened from home ends with 102: `clean` runs, then home again."""
    done = _bash(tmp_path, "mh", ("104", "102"))
    assert _lines(done) == [
        "home:relayed",
        "browse:relayed",
        "ran:clean",
        "home:relayed",
        "status=0",
    ]


@pytest.mark.parametrize("ended", ["0", "1", "125"])
def test_browse_closed_or_failed_goes_back_home(tmp_path: Path, ended: str) -> None:
    """0243: browse closed (⌂ Home), failed, or a code naming no step: home again."""
    done = _bash(tmp_path, "mh", ("104", ended))
    assert _lines(done) == [
        "home:relayed",
        "browse:relayed",
        "home:relayed",
        "status=0",
    ]


def test_browse_typed_alone_does_not_relay(tmp_path: Path) -> None:
    """`mh browse` alone: nobody would run its step, so no Apply now."""
    done = _bash(tmp_path, "mh browse", "")
    assert _lines(done) == ["browse:alone", "status=0"]


def test_home_typed_alone_does_not_relay(tmp_path: Path) -> None:
    """`mh home` has no loop to read the code: the page copies the command instead."""
    done = _bash(tmp_path, "mh home", "")
    assert _lines(done) == ["home:alone", "status=0"]


def test_powershell_holds_the_same_loop_in_ascii() -> None:
    """mh.ps1: home relayed by the loop only, the step read from the menu, then home."""
    with using(Locale.FR):
        text = render_script(launcher_script(accented_runtime(), None, _COMMANDS))
    assert text.isascii()
    alone = text.index("    if ($rest.Count -eq 0) {")
    assert text.index("        _mh_home @typed", alone) < text.index("docker run --rm")
    assert "function global:_mh_home {" in text
    assert (
        "        try { mh home @typed } finally { $global:MediaHygieneRelay = $null }"
        in text
    )
    assert "        if ($status -le 100) { return }" in text
    assert (
        "$relay = @(if ($global:MediaHygieneRelay -and $command -in @('home', "
        f"'browse')) {{ '-e', '{_RELAY}' }})"
    ) in text
    # 0243: a page a step opened (browse) may end on a step, run next.
    assert (
        "        try { mh @words @typed } finally { $global:MediaHygieneRelay = $null }"
        in text
    )
    assert "        if (-not $chosen -and $after) { $status = 0; continue }" in text
    assert "            @relay `" in text


def test_a_page_whose_tab_was_closed_ends_the_loop(tmp_path: Path) -> None:
    """0262: browse opened from home, its tab closed: prompt back, home not again."""
    done = _bash(tmp_path, "mh", ("104", str(int(ExitCode.PAGE_CLOSED))))
    assert _lines(done) == ["home:relayed", "browse:relayed", "status=0"]


def test_the_powershell_loop_ends_on_a_closed_page(tmp_path: Path) -> None:
    """0262: the same rule in mh.ps1, before home would open again."""
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    text = render_script(launcher_script(runtime, Shell.POWERSHELL, _COMMANDS))
    code = int(ExitCode.PAGE_CLOSED)
    closed = f"if ($status -eq {code}) {{ $global:LASTEXITCODE = 0; return }}"
    assert text.index(closed) < text.index("if ($status -le 100) {")
