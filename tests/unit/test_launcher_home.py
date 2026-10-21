"""`mh` alone: the home page; a step chosen there runs here, then the page again.

TODO 0210. `home` ends with `100 + n` for step `n` (0209) only when the launcher says
it relays the steps: `-e MEDIA_HYGIENE_LAUNCHER_STEPS=1`, set by this loop alone.
"""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.constants import ExitCode, Locale
from media_hygiene.i18n import using
from media_hygiene.paths.docker_run import Shell
from media_hygiene.paths.mounts import MountTable
from media_hygiene.review.home_fields import RELAY_FIELDS, write_step
from media_hygiene.review.home_views import FIELDS_STEP, STEP_EXIT_BASE
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

_COMMANDS: Final = LauncherCommands(
    names=("audit", "browse", "clean", "history", "home", "menu", "review"),
    writers=("clean",),
    pages=("home", "browse", "review"),
    data=("menu",),
    port=8088,
)
# The reports are in a host folder: `mh` also reads the one-shot file of a form (0266).
_RELAY: Final = f"{LAUNCHER_STEPS_VARIABLE}={RELAY_FIELDS}"
# `menu` prints its steps; `home` exits with the next code of $CODES (then 0) and
# says whether it was told to relay; any other command says it ran.
_FAKE_DOCKER: Final = r"""
docker() {
    if [[ "$1" == version ]]; then return 0; fi
    if [[ " $* " == *" menu "* ]]; then
        printf '0\taudit\n1\taudit\n2\tclean --tier near\n3\thistory\n'
        printf '4\tbrowse\n5\treview\n'
        return 0
    fi
    if [[ " $* " == *" review "* ]]; then
        sleep 0.3  # a page serves a while: its tab, if any, is opened meanwhile
        if [[ " $* " == *" -e RELAY "* ]]; then
            echo "review:relayed"
        else
            echo "review:alone"
        fi
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
        sleep 0.3  # a page serves a while: its tab, if any, is opened meanwhile
        if [[ " $* " == *" -e RELAY "* ]]; then
            echo "home:relayed"
        else
            echo "home:alone"
        fi
        return "${code:-0}"
    fi
    local words=() seen=""
    for arg in "$@"; do
        if [[ "$arg" == history || "$arg" == clean ]]; then echo "ran:$arg"; fi
        if [[ "$arg" == album ]]; then seen=1; fi
        if [[ -n "$seen" ]]; then words+=("$arg"); fi
    done
    if [[ -n "$seen" ]]; then (IFS='|'; echo "ran:${words[*]}"); fi
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
    # Each tab mh opens is one line of `tabs` (0280), instead of a browser.
    tab = '_mh_browse() { echo tab >> "$HOME/tabs"; }'
    code = f"{fake}\nsource {script}; {tab}; {line}; echo status=$?"
    return run_bash(code, {"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"})


def _tabs(tmp_path: Path) -> int:
    """How many browser tabs mh opened."""
    tabs = tmp_path / "tabs"
    return len(tabs.read_text().splitlines()) if tabs.exists() else 0


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


def test_one_tab_for_the_home_page_and_the_pages_it_opens(tmp_path: Path) -> None:
    """0280: home opens the tab; review and home again show in it, no new tab."""
    done = _bash(tmp_path, "mh", "105 103")
    assert _lines(done) == [
        "home:relayed",
        "review:relayed",
        "home:relayed",
        "ran:history",
        "home:relayed",
        "status=0",
    ]
    assert _tabs(tmp_path) == 1


def test_a_console_step_rings_the_bell_a_page_does_not(tmp_path: Path) -> None:
    """0285: BEL before `history` (it may ask), none before `review` (a page)."""
    console = _bash(tmp_path, "mh", "103")
    assert console.stderr.count("\a") == 1
    page = _bash(tmp_path, "mh", "105")
    assert "\a" not in page.stderr


def test_a_page_typed_alone_opens_its_tab_without_the_home_link(tmp_path: Path) -> None:
    """`mh review` alone: its own tab, and no relay (no "Back to the home page")."""
    done = _bash(tmp_path, "mh review", "")
    assert _lines(done) == ["review:alone", "status=0"]
    assert _tabs(tmp_path) == 1


def test_powershell_holds_the_same_loop_in_ascii() -> None:
    """mh.ps1: home relayed by the loop only, the step read from the menu, then home."""
    with using(Locale.FR):
        text = render_script(launcher_script(accented_runtime(), None, _COMMANDS))
    assert text.isascii()
    alone = text.index("    if ($rest.Count -eq 0) {")
    assert text.index("        _mh_home @typed", alone) < text.index("docker run --rm")
    assert "function global:_mh_home {" in text
    assert (
        "            try { mh home @typed } finally { "
        "$global:MediaHygieneRelay = $null; $global:MediaHygieneTab = $null }" in text
    )
    assert "        if ($status -le 100) { return }" in text
    assert (
        "$relay = @(if ($global:MediaHygieneRelay -and $command -in @('home', "
        f"'browse', 'review')) {{ '-e', '{_RELAY}' }})"
    ) in text
    # 0285: a console step brings this window forward (COM, no Add-Type), a page not.
    forward = text[text.index("function global:_mh_forward($command) {") :]
    forward = forward[: forward.index("\n}\n")]
    assert "if ($command -in @('home', 'browse', 'review')) { return }" in forward
    assert "(New-Object -ComObject WScript.Shell)" not in forward  # one object, kept
    assert "$shell = New-Object -ComObject WScript.Shell" in forward
    assert "if (-not $shell.AppActivate($PID))" in forward
    # Measured 2026-10-21: AppActivate does nothing in Windows Terminal; the bell (its
    # taskbar button flashes with bellStyle "taskbar") and the sound come first.
    bell = forward.index("Write-Host -NoNewline ([char]7)")
    assert bell < forward.index("[Media.SystemSounds]::Exclamation.Play()")
    assert bell < forward.index("AppActivate")
    assert "Add-Type" not in forward
    assert text.count('\n        _mh_forward "$($words[0])"') == 1  # a menu step
    assert text.count('\n            _mh_forward "$($words[0])"') == 1  # a form's step
    # 0280: one tab, opened by the first page of the loop; later pages show in it.
    assert "        if ($page -and -not $global:MediaHygieneTab) {" in text
    assert "            $tab = $true" in text
    # 0243: a page a step opened (browse) may end on a step, run next.
    assert (
        "        try { mh @words @typed } finally { $global:MediaHygieneRelay = $null;"
        " $global:MediaHygieneTab = $null }" in text
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


def _step_file(tmp_path: Path) -> Path:
    """Where the bash `mh` of `_bash` reads the words of a form (the reports folder)."""
    script = (tmp_path / "mh.sh").read_text()
    found = re.search(r'-f "([^"]+\.mh-step\.json)"', script)
    assert found
    return Path(found[1].replace("$HOME", str(tmp_path)))


def test_a_form_s_words_run_once_then_the_file_is_gone(tmp_path: Path) -> None:
    """0266: `199` runs the words of the one-shot file, `Noël 2025` one of them."""
    _bash(tmp_path, "true", "0")
    step = _step_file(tmp_path)
    step.parent.mkdir(parents=True, exist_ok=True)
    write_step(step.parent, ("album", "Noël 2025", "--category", "Noël"))
    code = str(STEP_EXIT_BASE + FIELDS_STEP)
    done = _bash(tmp_path, "mh", code)
    assert _lines(done) == [
        "home:relayed",
        "ran:album|Noël 2025|--category|Noël",
        "home:relayed",
        "status=0",
    ]
    assert not step.exists()


def test_a_file_left_behind_never_runs_for_a_numbered_step(tmp_path: Path) -> None:
    """A step chosen by its number runs that step, whatever file is there."""
    _bash(tmp_path, "true", "0")
    step = _step_file(tmp_path)
    step.parent.mkdir(parents=True, exist_ok=True)
    write_step(step.parent, ("album", "Old", "--category", "Old"))
    done = _bash(tmp_path, "mh", "103")
    assert _lines(done) == ["home:relayed", "ran:history", "home:relayed", "status=0"]
    assert step.exists()
