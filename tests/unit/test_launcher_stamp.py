"""`mh` says when its own file was written by another image (0290).

The script passes the stamp of the image that wrote it with `-e`; the image compares it
with its own and names `mh update` when they differ, or when the script passes none.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError
from typing import TYPE_CHECKING, Final

import pytest
from typer.testing import CliRunner

from media_hygiene.cli.app import build_app
from media_hygiene.paths.docker_run import Shell
from media_hygiene.services import launcher_stamp
from media_hygiene.services.launcher import (
    LauncherCommands,
    launcher_script,
    render_script,
)
from media_hygiene.services.launcher_stamp import (
    LAUNCHER_STAMP_VARIABLE,
    image_stamp,
    stamp_line,
)
from media_hygiene.services.next_command import LAUNCHER_VARIABLE, environment
from tests.unit.test_launcher_ascii import accented_runtime

if TYPE_CHECKING:
    from pathlib import Path

_STAMP: Final = "0.4.0+1a2b3c4d5e6f"
_SAID: Final = "update to write it again, with the same folders."
_COMMANDS: Final = LauncherCommands(("audit", "menu"), (), (), ("menu",), 8088)


@dataclass(frozen=True, slots=True)
class _Installed:
    """A stand-in for the installed distribution."""

    version: str
    record: str | None

    def read_text(self, name: str) -> str | None:
        """The `RECORD` given, whatever the name asked."""
        assert name == "RECORD"
        return self.record


def test_not_run_by_mh_or_the_same_image_says_nothing() -> None:
    """Typed `docker run`, the same stamp, an image without one: no line."""
    assert not stamp_line({}, _STAMP)
    assert not stamp_line({LAUNCHER_VARIABLE: "powershell"}, "")
    same = {LAUNCHER_VARIABLE: "powershell", LAUNCHER_STAMP_VARIABLE: _STAMP}
    assert not stamp_line(same, _STAMP)


def test_another_build_names_both_and_mh_update() -> None:
    """Same version, other code: both builds shown, the command named."""
    other = {LAUNCHER_VARIABLE: "bash", LAUNCHER_STAMP_VARIABLE: "0.4.0+ffffffffffff"}
    assert stamp_line(other, _STAMP) == (
        "This mh was written by the image 0.4.0 (build ffffffffffff), this one is "
        "0.4.0 (build 1a2b3c4d5e6f): type mh update to write it again, with the "
        "same folders."
    )


def test_an_mh_without_stamp_was_written_before_the_check() -> None:
    """0287's case: an mh.ps1 of an older image passes no stamp: said, too."""
    line = stamp_line({LAUNCHER_VARIABLE: "powershell"}, "0.4.0")
    assert line == (
        "This mh was written by an older image than 0.4.0: type mh update to write "
        "it again, with the same folders."
    )


def test_the_stamp_is_the_version_and_the_digest_of_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Other files, other stamp; same files, same stamp; no RECORD: the version."""

    def installed(record: str | None) -> None:
        monkeypatch.setattr(
            launcher_stamp, "distribution", lambda _name: _Installed("1.2.3", record)
        )

    installed("a.py,sha256=x,1\n")
    first = image_stamp()
    assert first.startswith("1.2.3+")
    assert len(first) == len("1.2.3+") + 12
    assert image_stamp() == first
    installed("a.py,sha256=y,1\n")
    assert image_stamp() != first
    installed(None)
    assert image_stamp() == "1.2.3"


def test_no_installed_package_no_stamp(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run from a tree without metadata: no stamp, so never a line."""

    def missing(name: str) -> None:
        raise PackageNotFoundError(name)

    monkeypatch.setattr(launcher_stamp, "distribution", missing)
    assert not image_stamp()


@pytest.mark.parametrize("shell", list(Shell))
def test_the_script_passes_its_stamp_to_each_run(shell: Shell) -> None:
    """Both shells write the stamp of the image that wrote them."""
    text = render_script(launcher_script(accented_runtime(), shell, _COMMANDS))
    assert f'-e "{LAUNCHER_STAMP_VARIABLE}={image_stamp()}"' in text


def test_the_stamp_is_never_carried_into_the_next_script(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`launcher` run by `mh` keeps the settings, not mh's own variables."""
    monkeypatch.setenv(LAUNCHER_STAMP_VARIABLE, _STAMP)
    monkeypatch.setenv(LAUNCHER_VARIABLE, "bash")
    monkeypatch.setenv("MEDIA_HYGIENE_REVIEW__PORT", "8099")
    kept = environment()
    assert '-e "MEDIA_HYGIENE_REVIEW__PORT=8099"' in kept
    assert not [option for option in kept if "LAUNCHER" in option]


@pytest.mark.parametrize("command", ["history", "menu"])
def test_said_by_commands_never_in_output_mh_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command: str
) -> None:
    """A data command (`menu`, `launcher`): its output is read, nothing added."""
    for name in ("CONFIG", "JOURNAL", "QUARANTINE", "REPORTS", "CACHE"):
        monkeypatch.setenv(f"MEDIA_HYGIENE_{name}_DIR", str(tmp_path / name))
    monkeypatch.setenv(LAUNCHER_VARIABLE, "bash")
    monkeypatch.delenv(LAUNCHER_STAMP_VARIABLE, raising=False)
    result = CliRunner().invoke(build_app(), [command])
    assert result.exit_code == 0, result.output
    said = " ".join((result.stdout + result.stderr).split())
    assert (_SAID in said) is (command == "history" and bool(image_stamp()))
