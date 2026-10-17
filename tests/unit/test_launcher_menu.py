"""`mh menu`: `menu` lists the steps, the number read runs as `mh <step>` (0172).

`mh` alone opens the home page instead (0210, `test_launcher_home.py`).
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import replace
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.paths.docker_run import Shell
from media_hygiene.paths.mounts import MountTable
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_menu import UNSAFE_CHARACTERS, menu_texts
from tests.support.runtime import make_locations, make_runtime
from tests.unit.test_launcher_ascii import accented_runtime, expanded

if TYPE_CHECKING:
    from pathlib import Path

_COMMANDS: Final = LauncherCommands(
    names=("audit", "clean", "history", "menu"),
    writers=("clean",),
    pages=(),
    data=("menu",),
    port=8088,
)
# `docker` stands in for the image: `menu` prints its steps, any other command
# prints the arguments it was given, one per line.
_FAKE_DOCKER: Final = r"""
docker() {
    if [[ " $* " == *" menu "* ]]; then
        echo "menu: $*" >&2
        printf '0\taudit\n1\taudit\n2\tclean --tier near --decisions\n3\thistory\n'
        return 0
    fi
    printf 'ran:%s\n' "$@"
}
"""


def _bash(tmp_path: Path, typed: str) -> subprocess.CompletedProcess[str]:
    """Load the bash `mh`, call `mh menu` and type a choice.

    Args:
        tmp_path: The test's folder, for the script and the home.
        typed: What the user types at the prompt.

    Returns:
        The finished bash.
    """
    runtime = replace(
        make_runtime(make_locations(tmp_path)), mounts=MountTable(frozenset())
    )
    script = tmp_path / "mh.sh"
    script.write_text(render_script(launcher_script(runtime, Shell.BASH, _COMMANDS)))
    bash = shutil.which("bash") or "bash"
    line = f"{_FAKE_DOCKER}\nsource {script}; mh menu; echo status=$?"
    # Trusted script written by the test itself, run on its temporary folder.
    return subprocess.run(  # noqa: S603
        [bash, "-c", line],
        input=typed,
        capture_output=True,
        text=True,
        check=False,
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"},
    )


def test_enter_runs_the_proposed_step_through_mh(tmp_path: Path) -> None:
    """Enter: line 0, run by mh itself; the menu ran without -i nor -t."""
    done = _bash(tmp_path, "\n")
    assert "status=0" in done.stdout
    assert "ran:audit" in done.stdout
    assert "Next time, type it directly: mh audit" in done.stderr
    menu = next(line for line in done.stderr.splitlines() if line.startswith("menu:"))
    assert " -i " not in menu
    assert " -it " not in menu


def test_a_number_runs_that_step_word_by_word(tmp_path: Path) -> None:
    """A number: its command split into words; clean mounts the photos writable."""
    done = _bash(tmp_path, "2\n")
    ran = [line for line in done.stdout.splitlines() if line.startswith("ran:")]
    assert ran[-4:] == ["ran:clean", "ran:--tier", "ran:near", "ran:--decisions"]
    assert not any(line.endswith(":ro") for line in ran)


def test_a_wrong_number_runs_nothing(tmp_path: Path) -> None:
    """No such step: said, status 2, nothing run."""
    done = _bash(tmp_path, "42\n")
    assert "status=2" in done.stdout
    assert "No step 42: type mh menu to see the menu again." in done.stderr
    assert "ran:" not in done.stdout


def test_powershell_menu_reads_a_number_then_calls_itself() -> None:
    """`mh menu`: menu captured, Read-Host, then mh @words; ASCII even in French."""
    with using(Locale.FR):
        text = render_script(launcher_script(accented_runtime(), None, _COMMANDS))
    assert text.isascii()
    assert "    if ($rest.Count -eq 1 -and $rest[0] -eq 'menu') {" in text
    assert "$steps = @(mh @color menu)" in text
    assert '$number, $line = "$step" -split "`t", 2' in text
    assert "    mh @words @typed" in text
    back = expanded(text)
    assert 'Write-Host "La prochaine fois, tapez-la directement : mh ${chosen}"' in back


def test_no_translation_can_break_the_script() -> None:
    """Neither quote, dollar of its own, backtick nor backslash, in both languages."""
    for locale in Locale:
        with using(locale):
            texts = menu_texts()
        for text in (texts.prompt, texts.unknown, texts.direct):
            own = text.replace("${choice}", "").replace("${chosen}", "")
            assert not set(own) & UNSAFE_CHARACTERS
