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
    """Above the lines of `status`, in bold."""
    page = home_page(relays_steps=True).decode()
    assert '...state.given.map((line) => element("li", line, "given"))' in page
    assert "#where li.given { font-weight: 600; }" in page


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
    assert _texts(page)["runningWhere"] == (
        f"{{command}} runs in {window}: this page comes back by itself when it ends."
    )
    text = page.decode()
    assert f'<p id="runningHint" hidden>Nothing moves? Look at {window} (Alt+Tab).' in (
        text
    )
    assert "const HINT_MS = 30000;" in text
    wait = text.index("const waitForComeBack = () => {")
    shown = text.index('byId("runningHint").hidden = false; }, HINT_MS);')
    assert wait < shown < text.index("const poll = () => {", wait)
    assert "Running in the window where mh runs" not in text


def test_the_window_is_translated(monkeypatch: pytest.MonkeyPatch) -> None:
    """French page: the PowerShell window named in French."""
    monkeypatch.setenv(LAUNCHER_VARIABLE, Shell.POWERSHELL.value)
    with using(Locale.FR):
        page = home_page(relays_steps=True)
    assert _texts(page)["runningWhere"] == (
        "{command} tourne dans la fenêtre PowerShell de mh (dans la barre des "
        "tâches) : cette page revient d'elle-même quand c'est fini."
    )
