"""An unexpected error: a few calm lines and the failure code, never a traceback."""

from __future__ import annotations

import sys

import pytest
import typer
from typer.testing import CliRunner

from media_hygiene.cli.app import build_app
from media_hygiene.cli.localized import LocalizedGroup
from media_hygiene.cli.unexpected import DEBUG_VARIABLE, ISSUES
from media_hygiene.constants import ExitCode

_TRACEBACK = "Traceback"


def _failing_app() -> typer.Typer:
    """An app whose commands fail like a bug would, or exit on purpose.

    Returns:
        The app, built with the root group of the real CLI.
    """
    app = typer.Typer(cls=LocalizedGroup, pretty_exceptions_enable=False)

    def _bug() -> None:
        message = "cell value <x00> is illegal"
        raise RuntimeError(message)

    def _exit() -> None:
        raise typer.Exit(ExitCode.USAGE)

    for name in ("inventory", "clean", "purge", "home"):
        app.command(name=name)(_bug)
    app.command(name="done")(_exit)
    return app


def _flat(text: str) -> str:
    """The output on one line, whatever the console width."""
    return " ".join(text.split())


@pytest.fixture(autouse=True)
def _no_debug(monkeypatch: pytest.MonkeyPatch) -> None:
    """The developer's own MEDIA_HYGIENE_DEBUG does not leak into these tests."""
    monkeypatch.delenv(DEBUG_VARIABLE, raising=False)


@pytest.fixture(autouse=True)
def _own_command_line(monkeypatch: pytest.MonkeyPatch) -> None:
    """The message quotes `sys.argv`: never pytest's own (files named "undo")."""
    monkeypatch.setattr(sys, "argv", ["media-hygiene"])


def test_a_bug_in_a_read_only_command_is_one_calm_message() -> None:
    """What failed, the photos untouched, where to report it; the failure code."""
    result = CliRunner().invoke(_failing_app(), ["inventory"])
    assert result.exit_code == ExitCode.FAILURE
    text = _flat(result.output)
    assert _TRACEBACK not in text
    assert ".venv" not in text
    assert "site-packages" not in text
    assert "Unexpected error during inventory: RuntimeError:" in text
    assert "cell value <x00> is illegal" in text
    assert "Your photos and videos were not touched." in text
    assert ISSUES in text
    assert f"-e {DEBUG_VARIABLE}=1" in text


def test_a_bug_in_clean_points_to_undo_and_purge_promises_nothing() -> None:
    """`clean` keeps a journal; `purge` neither promises nor offers undo."""
    clean = _flat(CliRunner().invoke(_failing_app(), ["clean"]).output)
    assert "'undo' puts it back" in clean
    assert "not touched" not in clean
    purge = _flat(CliRunner().invoke(_failing_app(), ["purge"]).output)
    assert "undo" not in purge.replace(ISSUES, "")
    assert "not touched" not in purge


def test_debug_lets_the_exception_through(monkeypatch: pytest.MonkeyPatch) -> None:
    """`MEDIA_HYGIENE_DEBUG=1`: the developer gets the exception itself."""
    monkeypatch.setenv(DEBUG_VARIABLE, "1")
    with pytest.raises(RuntimeError, match="illegal"):
        CliRunner().invoke(_failing_app(), ["inventory"], catch_exceptions=False)


def test_exits_and_usage_errors_are_untouched() -> None:
    """`typer.Exit` keeps its code; a bad option is still Click's usage error."""
    done = CliRunner().invoke(_failing_app(), ["done"])
    assert done.exit_code == ExitCode.USAGE
    assert "Unexpected error" not in done.output
    usage = CliRunner().invoke(build_app(), ["audit", "--no-such-option"])
    assert usage.exit_code == ExitCode.USAGE
    assert "Unexpected error" not in usage.output


def test_a_bug_in_the_home_server_ends_with_its_own_code() -> None:
    """0365: `home` alone ends with `CRASHED`, so that `mh` starts it again."""
    result = CliRunner().invoke(_failing_app(), ["home"])
    assert result.exit_code == ExitCode.CRASHED
    assert ISSUES in _flat(result.output)
