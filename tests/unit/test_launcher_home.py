"""`mh` alone: the home page; a step chosen there runs here, then the page again.

TODO 0210. `home` ends with `STEP_EXIT_BASE + n` for step `n` (0209) only when the
launcher says it relays the steps: `-e MEDIA_HYGIENE_LAUNCHER_STEPS=1`, set by this loop
alone.
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
from media_hygiene.review.home_views import (
    FIELDS_STEP,
    SIGNAL_EXIT_BASE,
    STEP_EXIT_BASE,
)
from media_hygiene.review.step_watch import WATCH
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
# The home server kept up in the background, the steps run beside it (0355).
_KEPT: Final = f"{LAUNCHER_STEPS_VARIABLE}={WATCH.kept}"
# `menu` prints its steps; `home` exits with the next code of $CODES (then 0) and
# says whether it was told to relay; any other command says it ran.
_FAKE_DOCKER: Final = r"""
said() { echo "$1" >> "$HOME/said"; }  # what the fake image did, in order
docker() {
    if [[ "$1" == version ]]; then return 0; fi
    if [[ "$1" == stop ]]; then said "stopped:$2"; return 0; fi
    if [[ "$1" == wait ]]; then
        # The page asks the console steps of $HOME/asks one by one (0355), each once
        # the last is done; then the server ends with the code `run -d` kept.
        local asked step=0 tries
        if [[ -s "$HOME/asks" ]]; then
            while IFS= read -r asked; do
                step=$((step + 1))
                printf '{\n"id": "s%d",\n"words": [\n"%s"\n]\n}\n' \
                    "$step" "$asked" > "$MH_NOW"
                for tries in $(seq 50); do
                    if grep -qs "\"s$step\"" "$MH_DONE"; then break; fi
                    sleep 0.1
                done
            done < "$HOME/asks"
        fi
        sleep 0.2
        cat "$HOME/home-code"
        return 0
    fi
    if [[ " $* " == *" menu "* ]]; then
        echo menu >> "$HOME/menus"  # each `mh menu` container (0354)
        printf '0\taudit\n1\taudit\n2\tclean --tier near\n3\thistory\n'
        printf '4\tbrowse\n5\treview\n'
        printf '110\thistory\n'  # 20 + 110 = 130: Ctrl+C must never run it (0287)
        return 0
    fi
    if [[ " $* " == *" review "* ]]; then
        sleep 0.3  # a page serves a while: its tab, if any, is opened meanwhile
        if [[ " $* " == *" -e RELAY "* ]]; then
            said "review:relayed"
        else
            said "review:alone"
        fi
        return 0
    fi
    if [[ " $* " == *" browse "* ]]; then
        local ended=0
        if [[ -s "$HOME/browse" ]]; then read -r ended < "$HOME/browse"; fi
        if [[ " $* " == *" -e RELAY "* ]]; then
            said "browse:relayed"
        else
            said "browse:alone"
        fi
        return "$ended"
    fi
    if [[ " $* " == *" home "* ]]; then
        local code=0 rest arg prev=""
        if [[ -s "$HOME/codes" ]]; then
            read -r code rest < "$HOME/codes"
            printf '%s\n' "$rest" > "$HOME/codes"
        fi
        if [[ " $* " == *" -d "* ]]; then
            # In the background (0355): its id in --cidfile, its code for `docker wait`.
            for arg in "$@"; do
                if [[ "$prev" == --cidfile ]]; then echo "home1" > "$arg"; fi
                prev="$arg"
            done
            echo "${code:-0}" > "$HOME/home-code"
            echo "home1"
            if [[ " $* " == *" -e KEPT "* ]]; then said "home:relayed"; return 0; fi
            said "home:alone"
            return 0
        fi
        sleep 0.3  # a page serves a while: its tab, if any, is opened meanwhile
        if [[ " $* " == *" -e RELAY "* ]]; then
            said "home:relayed"
        else
            said "home:alone"
        fi
        return "${code:-0}"
    fi
    local words=() seen=""
    for arg in "$@"; do
        if [[ "$arg" == history || "$arg" == clean ]]; then said "ran:$arg"; fi
        if [[ "$arg" == album ]]; then seen=1; fi
        if [[ -n "$seen" ]]; then words+=("$arg"); fi
    done
    if [[ -n "$seen" ]]; then (IFS='|'; said "ran:${words[*]}"); fi
    local ended=0  # a step ends with the code of `ran` (Ctrl+C during it: 130)
    if [[ -s "$HOME/ran" ]]; then read -r ended < "$HOME/ran"; fi
    return "$ended"
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
    fake = _FAKE_DOCKER.replace("RELAY", _RELAY).replace("KEPT", _KEPT)
    # Each tab mh opens is one line of `tabs` (0280), instead of a browser.
    tab = '_mh_browse() { echo tab >> "$HOME/tabs"; }'
    said = tmp_path / "said"
    said.unlink(missing_ok=True)
    code = (
        f"{fake}\nsource {script}; {tab}; {line}; s=$?; "
        f'cat "{said}" 2>/dev/null; echo status=$s'
    )
    reports = Path(_step_path(script).replace("$HOME", str(tmp_path))).parent
    steps = {
        "HOME": str(tmp_path),
        "PATH": "/usr/bin:/bin",
        "MH_NOW": str(reports / WATCH.now),
        "MH_DONE": str(reports / WATCH.done),
    }
    return run_bash(code, steps)


def _code(*numbers: int) -> str:
    """The codes `home` ends with when steps `numbers` are chosen, in turn."""
    return " ".join(str(STEP_EXIT_BASE + number) for number in numbers)


def _tabs(tmp_path: Path) -> int:
    """How many browser tabs mh opened."""
    tabs = tmp_path / "tabs"
    return len(tabs.read_text().splitlines()) if tabs.exists() else 0


def _lines(done: subprocess.CompletedProcess[str]) -> list[str]:
    """What the fake image said, in order, and the final status."""
    return [line for line in done.stdout.splitlines() if ":" in line or "=" in line]


def test_a_step_chosen_runs_then_the_page_comes_back(tmp_path: Path) -> None:
    """Step 3 (`history`) runs, then `home` again, which ends with 0."""
    done = _bash(tmp_path, "mh", _code(3))
    assert _lines(done) == ["home:relayed", "ran:history", "home:relayed", "status=0"]
    assert "Next time, type it directly: mh history" in done.stderr


def test_two_steps_in_a_row(tmp_path: Path) -> None:
    """Each step chosen runs in turn; a writer gets the photos writable."""
    done = _bash(tmp_path, "mh", _code(2, 3))
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
    """0243: browse opened from home ends on step 2: `clean` runs, then home again."""
    done = _bash(tmp_path, "mh", (_code(4), _code(2)))
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
    done = _bash(tmp_path, "mh", (_code(4), ended))
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
    done = _bash(tmp_path, "mh", _code(5, 3))
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
    console = _bash(tmp_path, "mh", _code(3))
    assert console.stderr.count("\a") == 1
    page = _bash(tmp_path, "mh", _code(5))
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
        "            try { _mh_watch @typed } finally { "
        "$global:MediaHygieneRelay = $null; $global:MediaHygieneTab = $null }" in text
    )
    assert (
        f"        if ($status -le {STEP_EXIT_BASE} -or $status -ge {SIGNAL_EXIT_BASE})"
        " { return }"
    ) in text
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
    # A form's step, and a console step the server kept up for (0355).
    assert text.count('\n            _mh_forward "$($words[0])"') == 2
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
    done = _bash(tmp_path, "mh", (_code(4), str(int(ExitCode.PAGE_CLOSED))))
    assert _lines(done) == ["home:relayed", "browse:relayed", "status=0"]


def test_the_powershell_loop_ends_on_a_closed_page(tmp_path: Path) -> None:
    """0262: the same rule in mh.ps1, before home would open again."""
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    text = render_script(launcher_script(runtime, Shell.POWERSHELL, _COMMANDS))
    code = int(ExitCode.PAGE_CLOSED)
    closed = f"if ($status -eq {code}) {{ $global:LASTEXITCODE = 0; return }}"
    assert text.index(closed) < text.index(f"if ($status -le {STEP_EXIT_BASE}) {{")


def _step_path(script: Path) -> str:
    """The one-shot file's path as the bash `mh` names it, `$HOME` unexpanded."""
    found = re.search(r'-f "([^"]+\.mh-step\.json)"', script.read_text())
    assert found
    return found[1]


def _step_file(tmp_path: Path) -> Path:
    """Where the bash `mh` of `_bash` reads the words of a form (the reports folder)."""
    return Path(_step_path(tmp_path / "mh.sh").replace("$HOME", str(tmp_path)))


def test_a_form_s_words_run_once_then_the_file_is_gone(tmp_path: Path) -> None:
    """0266: the fields code runs the one-shot file's words, `Noël 2025` one of them."""
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


def test_a_page_chosen_runs_from_the_file_without_mh_menu_nor_bell(
    tmp_path: Path,
) -> None:
    """0354: a step from the file: no `mh menu` container; a page rings no bell."""
    _bash(tmp_path, "true", "0")
    step = _step_file(tmp_path)
    step.parent.mkdir(parents=True, exist_ok=True)
    write_step(step.parent, ("browse",))
    done = _bash(tmp_path, "mh", str(STEP_EXIT_BASE + FIELDS_STEP))
    assert _lines(done) == [
        "home:relayed",
        "browse:relayed",
        "home:relayed",
        "status=0",
    ]
    assert not (tmp_path / "menus").exists()
    assert "\a" not in done.stderr
    assert not step.exists()


def test_a_console_step_from_the_file_rings_the_bell(tmp_path: Path) -> None:
    """0285 kept: a step that asks in the terminal rings it, as from `mh menu`."""
    _bash(tmp_path, "true", "0")
    step = _step_file(tmp_path)
    step.parent.mkdir(parents=True, exist_ok=True)
    write_step(step.parent, ("history",))
    done = _bash(tmp_path, "mh", str(STEP_EXIT_BASE + FIELDS_STEP))
    assert "ran:history" in _lines(done)
    assert "\a" in done.stderr


def test_a_file_left_behind_never_runs_for_a_numbered_step(tmp_path: Path) -> None:
    """A step chosen by its number runs that step, whatever file is there."""
    _bash(tmp_path, "true", "0")
    step = _step_file(tmp_path)
    step.parent.mkdir(parents=True, exist_ok=True)
    write_step(step.parent, ("album", "Old", "--category", "Old"))
    done = _bash(tmp_path, "mh", _code(3))
    assert _lines(done) == ["home:relayed", "ran:history", "home:relayed", "status=0"]
    assert step.exists()


_SIGNALS: Final = (int(ExitCode.INTERRUPTED), SIGNAL_EXIT_BASE + 15)  # Ctrl+C, SIGTERM


def test_the_step_range_never_reaches_a_signal_s_code() -> None:
    """0287: every step code, the form's included, sits below Docker's and the signals'.

    Above the tool's own codes (0-3), below 125 (Docker's own, then 128 + n): Ctrl+C
    (130) can never name a step, and a menu longer than `FIELDS_STEP` steps fails here.
    """
    docker_codes = 125
    assert max(code for code in ExitCode if code < SIGNAL_EXIT_BASE) < STEP_EXIT_BASE
    assert STEP_EXIT_BASE + FIELDS_STEP < docker_codes <= SIGNAL_EXIT_BASE
    assert ExitCode.INTERRUPTED >= SIGNAL_EXIT_BASE


@pytest.mark.parametrize("code", _SIGNALS)
def test_ctrl_c_on_home_ends_the_loop(tmp_path: Path, code: int) -> None:
    """0287: home interrupted: prompt back with its code, no step, home not again."""
    done = _bash(tmp_path, "mh", str(code))
    assert _lines(done) == ["home:relayed", f"status={code}"]


@pytest.mark.parametrize("code", _SIGNALS)
def test_ctrl_c_during_a_step_ends_the_loop(tmp_path: Path, code: int) -> None:
    """0287: a step interrupted (history, or a page it opened): home not again."""
    (tmp_path / "ran").write_text(f"{code}\n")
    done = _bash(tmp_path, "mh", _code(3))
    assert _lines(done) == ["home:relayed", "ran:history", f"status={code}"]
    browse = _bash(tmp_path, "mh", (_code(4), str(code)))
    assert _lines(browse) == ["home:relayed", "browse:relayed", f"status={code}"]


def test_the_powershell_loop_ends_on_a_signal_s_code(tmp_path: Path) -> None:
    """0287: mh.ps1 checks a signal's code before it would open home or read a step."""
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    text = render_script(launcher_script(runtime, Shell.POWERSHELL, _COMMANDS))
    ended = (
        f"if ($status -ge {SIGNAL_EXIT_BASE}) "
        "{ $global:LASTEXITCODE = $status; return }"
    )
    assert text.index(ended) < text.index(f"if ($status -le {STEP_EXIT_BASE}) {{")
    assert text.index(ended) < text.index("$steps = @(mh @color menu)")


def test_a_console_step_runs_while_the_server_stays_up(tmp_path: Path) -> None:
    """0355: the page asks `history`: it runs here, the server not started again."""
    (tmp_path / "asks").write_text("history\n")
    done = _bash(tmp_path, "mh", "0")
    assert _lines(done) == ["home:relayed", "ran:history", "status=0"]
    reports = _step_file(tmp_path).parent
    assert (reports / WATCH.done).read_text() == '{"id": "s1", "code": 0}\n'
    assert not (reports / WATCH.running).exists()
    assert not (reports / WATCH.now).exists()
    assert not (tmp_path / "menus").exists()


def test_a_page_step_still_ends_the_server_kept_up(tmp_path: Path) -> None:
    """0355: a page needs the port: the server ends, the page runs, then home again."""
    _bash(tmp_path, "true", "0")
    step = _step_file(tmp_path)
    step.parent.mkdir(parents=True, exist_ok=True)
    write_step(step.parent, ("browse",))
    done = _bash(tmp_path, "mh", str(STEP_EXIT_BASE + FIELDS_STEP))
    assert _lines(done) == [
        "home:relayed",
        "browse:relayed",
        "home:relayed",
        "status=0",
    ]


def test_powershell_watches_the_server_in_the_background(tmp_path: Path) -> None:
    """0355: started detached, its end seen without a docker call per poll, stopped."""
    runtime = make_runtime(make_locations(tmp_path))
    text = render_script(launcher_script(runtime, Shell.POWERSHELL, _COMMANDS))
    start = text.index("function global:_mh_watch {")
    watch = text[start : text.index("\n}\n", start)]
    assert "$global:MediaHygieneDetach = $cid" in watch
    assert "Start-Process -FilePath docker -ArgumentList 'wait', $id" in watch
    assert "while (-not $waiter.HasExited) {" in watch
    assert "Start-Sleep -Milliseconds 250" in watch
    assert watch.count("docker ") == 2  # wait, then stop on Ctrl+C: never per poll
    assert "if (-not $ended) { $null = docker stop $id" in watch
    assert "[IO.File]::WriteAllText($done," in watch  # no byte order mark
    assert "if ($detach) { $tty = @('-d', '--cidfile', $detach) }" in text
    assert f"if ($detach) {{ $relay = @('-e', '{_KEPT}') }}" in text


def test_an_audit_asking_for_the_gone_review_opens_it(tmp_path: Path) -> None:
    """The audit ends with GONE_REVIEW: a success, then `mh review --gone`."""
    (tmp_path / "ran").write_text(f"{int(ExitCode.GONE_REVIEW)}\n")
    done = _bash(tmp_path, "mh audit", "0")
    assert _lines(done) == ["review:alone", "status=0"]
    assert _tabs(tmp_path) == 1


def test_another_command_ending_with_that_code_opens_nothing(tmp_path: Path) -> None:
    """Only `audit` asks for the review: any other command keeps its code."""
    (tmp_path / "ran").write_text(f"{int(ExitCode.GONE_REVIEW)}\n")
    done = _bash(tmp_path, "mh history", "0")
    assert _lines(done) == ["ran:history", f"status={int(ExitCode.GONE_REVIEW)}"]


def test_powershell_opens_the_gone_review_after_the_audit(tmp_path: Path) -> None:
    """The same rule in mh.ps1: the audit's code made a success, then the page."""
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    text = render_script(launcher_script(runtime, Shell.POWERSHELL, _COMMANDS))
    code = int(ExitCode.GONE_REVIEW)
    asked = f"$follow = $command -eq 'audit' -and $status -eq {code}"
    assert text.index(asked) < text.index("if ($follow) { mh review --gone @typed }")


_CRASHED: Final = str(int(ExitCode.CRASHED))
_KILLED: Final = str(int(ExitCode.KILLED))


@pytest.mark.parametrize("code", [_CRASHED, _KILLED])
def test_a_crashed_home_server_starts_again_once(tmp_path: Path, code: str) -> None:
    """0365: a crash (its own code, Docker's kill) starts the page again, said once."""
    done = _bash(tmp_path, "mh", code)
    assert _lines(done) == ["home:relayed", "home:relayed", "status=0"]
    assert "stopped unexpectedly: started again" in done.stderr


def test_two_crashes_in_a_row_end_the_loop(tmp_path: Path) -> None:
    """0365: crashed again within a minute: the prompt back, with the reason."""
    done = _bash(tmp_path, "mh", f"{_CRASHED} {_KILLED}")
    assert _lines(done) == ["home:relayed", "home:relayed", f"status={_KILLED}"]
    assert "twice in a row" in done.stderr


def test_the_powershell_loop_starts_a_crashed_server_again(tmp_path: Path) -> None:
    """0365: the same rule in mh.ps1, before a code ends the loop."""
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    text = render_script(launcher_script(runtime, Shell.POWERSHELL, _COMMANDS))
    crashed = f"if (@({_CRASHED}, {_KILLED}) -contains $status) {{"
    ends = f"if ($status -le {STEP_EXIT_BASE} -or $status -ge {SIGNAL_EXIT_BASE})"
    assert text.index(crashed) < text.index(ends)
    assert "$crashed = Get-Date" in text
