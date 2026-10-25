"""The home page opened by a right-click names its folder; *Run* says which window.

TODO 0258, seen on 2026-10-19: a right-click on `L'ete 2019` opened the page, which
said nothing of that folder; after *Run* the maintainer did not know which window ran
the step, often behind the browser.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.cli.home_state import home_state
from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.paths.docker_run import Shell
from media_hygiene.services.home import home_page
from media_hygiene.services.launcher import launcher_script, render_script
from media_hygiene.services.next_command import (
    LAUNCHER_PHOTOS_VARIABLE,
    LAUNCHER_VARIABLE,
    environment,
)
from tests.support.runtime import make_locations, make_runtime
from tests.unit.test_launcher_ascii import accented_runtime
from tests.unit.test_launcher_launch import COMMANDS

if TYPE_CHECKING:
    from pathlib import Path

_FOLDERS: Final = ("C:\\Users\\me\\L'été 2019", "E:\\Photos")


def _texts(page: bytes) -> dict[str, str]:
    """The texts the page's script holds."""
    found = re.search(r"const T = (\{.*?\});\n", page.decode())
    assert found
    texts: dict[str, str] = json.loads(found[1])
    return texts


def test_mh_ps1_gives_the_page_the_folders_of_photos() -> None:
    """The relayed page gets `--photos`' host folders, `|` between them, in ASCII."""
    with using(Locale.FR):
        text = render_script(launcher_script(accented_runtime(), None, COMMANDS))
    assert text.isascii()
    relay = text.index("$relay = @(if ($global:MediaHygieneRelay")
    given = text.index(
        "    if ($relay -and $typed) { $relay += '-e', "
        f"('{LAUNCHER_PHOTOS_VARIABLE}=' + (@(for ($i = 1; $i -lt $typed.Count; "
        "$i += 2) { $typed[$i] }) -join '|')) }"
    )
    assert relay < given < text.index("            @relay `")


def test_the_page_names_each_folder_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One line per folder, in its own field; none without `--photos`."""
    runtime = make_runtime(make_locations(tmp_path))
    monkeypatch.delenv(LAUNCHER_PHOTOS_VARIABLE, raising=False)
    assert not home_state(runtime).given
    monkeypatch.setenv(LAUNCHER_PHOTOS_VARIABLE, "|".join(_FOLDERS))
    state = home_state(runtime)
    assert state.given == tuple(f"This page also analyses: {f}" for f in _FOLDERS)
    assert not set(state.given) & set(state.lines)
    with using(Locale.FR):
        assert home_state(runtime).given[0] == (
            f"Cette page analyse aussi : {_FOLDERS[0]}"
        )


def test_the_folders_variable_is_not_carried_to_the_next_commands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A suggested command never repeats the page's folders."""
    monkeypatch.setenv(LAUNCHER_PHOTOS_VARIABLE, _FOLDERS[1])
    assert not any(LAUNCHER_PHOTOS_VARIABLE in option for option in environment())


def test_the_given_folders_are_drawn_first() -> None:
    """Above the next step, each folder in its own callout."""
    page = home_page(relays_steps=True).decode()
    assert "S.given.map((line) =>" in page
    assert page.index("${given}${hero()}") > 0


@pytest.mark.parametrize(
    ("shell", "window"),
    [
        (Shell.POWERSHELL, "the PowerShell window of mh (in the taskbar)"),
        (Shell.BASH, "the terminal where mh runs"),
    ],
)
def test_run_says_which_window_then_a_hint_after_30_s(
    monkeypatch: pytest.MonkeyPatch, shell: Shell, window: str
) -> None:
    """The window named after *Run*; *Nothing moves?* shown 30 s later."""
    monkeypatch.setenv(LAUNCHER_VARIABLE, shell.value)
    page = home_page(relays_steps=True)
    texts = _texts(page)
    assert texts["runsConsole"] == (
        "{command} runs in {window}: answer it if it asks something, then this "
        "page comes back by itself."
    )
    assert texts["nothingMoves"] == "Nothing moves? Look at {window} (Alt+Tab)."
    text = page.decode()
    assert f"const WINDOW = {json.dumps(window)};" in text
    assert "const HINT_MS = 30000;" in text
    wait = text.index("function waitForComeBack(page, run) {")
    shown = text.index("hint.hidden = false; }, HINT_MS);", wait)
    assert wait < shown < text.index("const poll = () => {", wait)


def test_a_console_step_says_at_once_to_switch_to_the_window() -> None:
    """0285: the alert at once, for a console step only; the 30 s hint stays."""
    page = home_page(relays_steps=True)
    assert _texts(page)["switchNow"] == (
        "Switch to {window} now (Alt+Tab, or its button in the taskbar): it may "
        "ask you something."
    )
    text = page.decode()
    run = text.index("function openRun(action, command, run, kept) {")
    alert = text.index(
        '${action.kind === "page" ? "" : `<p class="dlg-alert" role="alert">', run
    )
    assert alert < text.index('id="runHint" hidden>', run)
    assert "fill(T.switchNow, { window: WINDOW })" in text


def test_the_page_says_the_stop_within_a_beat_never_during_a_step() -> None:
    """0284: a beat finding nobody shows the stop; not while a step or Quit runs."""
    text = home_page(relays_steps=True).decode()
    wire = text.index("function wirePresence() {")
    assert text.index(
        ".catch(() => { if (!leaving && !presence.away) stopped(); });", wire
    )
    assert 'document.addEventListener("visibilitychange"' in text[wire:]
    # A step the server stays up for (0355) keeps the beats: the page is not leaving.
    assert "if (!kept) presence.away = true;" in text[text.index("function openRun(") :]
    assert 'data-act="quit"' not in text
    assert _texts(home_page(relays_steps=True))["stoppedText"].startswith(
        "Its window was closed (or Ctrl+C was pressed in it)."
    )


def test_a_page_step_shows_in_this_tab_and_comes_back_to_this_section() -> None:
    """0280: no new tab; the tab keeps its section, then follows any page on "/"."""
    page = home_page(relays_steps=True)
    assert _texts(page)["runsPage"] == (
        "{command} opens its page here, in this tab; its ⌂ Back to the home page "
        "brings you back to this very place."
    )
    text = page.decode()
    run = text.index("function openRun(action, command, run, kept) {")
    kept = text.index(
        'sessionStorage.setItem("mh-home-section", window.location.hash)', run
    )
    assert kept < text.index('waitForComeBack(action.kind === "page", run);', run)
    wait = text.index("function waitForComeBack(page, run) {")
    polled = 'fetch("/", { cache: "no-store", signal: AbortSignal.timeout(ANSWER_MS) })'
    assert text.index(polled, wait) < text.index(
        'else if (page) window.location.replace("/");', wait
    )


def test_the_window_is_translated(monkeypatch: pytest.MonkeyPatch) -> None:
    """French page: the PowerShell window named in French."""
    monkeypatch.setenv(LAUNCHER_VARIABLE, Shell.POWERSHELL.value)
    with using(Locale.FR):
        page = home_page(relays_steps=True).decode()
    window = "la fenêtre PowerShell de mh (dans la barre des tâches)"
    assert f"const WINDOW = {json.dumps(window)};" in page
