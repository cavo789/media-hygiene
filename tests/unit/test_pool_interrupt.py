"""Ctrl+C while an image pool starts: a calm stop, never a traceback (0627)."""

from __future__ import annotations

import os
import signal
import sys
import time
from concurrent.futures.process import BrokenProcessPool
from multiprocessing import forkserver
from typing import TYPE_CHECKING, Any

import pytest
import typer
from typer.testing import CliRunner

from media_hygiene.cli.localized import LocalizedGroup
from media_hygiene.cli.unexpected import DEBUG_VARIABLE, named_error
from media_hygiene.constants import ExitCode
from media_hygiene.services import runtime
from media_hygiene.services.interrupt import broken_by_stop

if TYPE_CHECKING:
    from pathlib import Path

_GROUP = "tasks"
_SLOW_MODULE = """
import pathlib, time
pathlib.Path({marker!r}).touch()
time.sleep(1.0)
"""


def _wait_for(marker: Path) -> None:
    """Poll until the fork server reaches its slow import."""
    deadline = time.monotonic() + 30
    while not marker.exists():
        assert time.monotonic() < deadline, "the fork server never started"
        time.sleep(0.02)


def test_the_fork_server_survives_ctrl_c_during_its_preload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capfd: pytest.CaptureFixture[str]
) -> None:
    """SIGINT in the middle of the preload: the server lives on, nothing printed."""
    marker = tmp_path / "importing"
    (tmp_path / "slow_preload.py").write_text(_SLOW_MODULE.format(marker=str(marker)))
    monkeypatch.syspath_prepend(str(tmp_path))
    server: Any = forkserver.ForkServer()  # its pid and stop are private
    server.set_forkserver_preload(["media_hygiene.scan.calm_server", "slow_preload"])
    server.ensure_running()
    pid = server._forkserver_pid  # noqa: SLF001  # pylint: disable=protected-access
    assert pid is not None
    try:
        _wait_for(marker)
        os.kill(pid, signal.SIGINT)
        time.sleep(0.2)
        assert os.waitpid(pid, os.WNOHANG) == (0, 0)  # still alive
    finally:
        server._stop()  # noqa: SLF001  # pylint: disable=protected-access
    assert "Traceback" not in capfd.readouterr().err


def test_the_calm_module_comes_first_in_the_preload() -> None:
    """Before Pillow and numpy: the window of a Ctrl+C is closed first."""
    assert runtime._WORKER_MODULES[0] == "media_hygiene.scan.calm_server"  # noqa: SLF001  # pylint: disable=protected-access


@pytest.mark.parametrize(
    "error",
    [BrokenProcessPool("lost"), ExceptionGroup("tasks", [BrokenProcessPool("lost")])],
)
def test_a_pool_broken_after_a_stop_is_a_stop(error: BaseException) -> None:
    """Alone or in a task group, after Ctrl+C: a stop; without it: a real failure."""
    assert broken_by_stop(error, lambda: True)
    assert not broken_by_stop(error, lambda: False)


def test_another_error_after_a_stop_stays_an_error() -> None:
    """Only a broken pool is the doing of Ctrl+C."""
    group = ExceptionGroup("tasks", [ValueError("bug")])
    assert not broken_by_stop(group, lambda: True)
    assert not broken_by_stop(ValueError("bug"), lambda: True)


def test_a_one_exception_group_names_that_exception() -> None:
    """Nested one-exception groups: the real error is named."""
    inner = OSError("disk gone")
    assert named_error(ExceptionGroup("a", [ExceptionGroup("b", [inner])])) is inner
    several = ExceptionGroup("a", [OSError("x"), ValueError("y")])
    assert named_error(several) is several


def _group_app() -> typer.Typer:
    """An app whose commands end in task groups, like an asyncio run.

    Returns:
        The app, built with the root group of the real CLI.
    """
    app = typer.Typer(cls=LocalizedGroup, pretty_exceptions_enable=False)

    def _stopped() -> None:
        raise BaseExceptionGroup(_GROUP, [KeyboardInterrupt()])

    def _bug() -> None:
        raise ExceptionGroup(_GROUP, [OSError("disk gone")])

    app.command(name="inventory")(_stopped)
    app.command(name="clean")(_bug)
    return app


@pytest.fixture(autouse=True)
def _no_debug(monkeypatch: pytest.MonkeyPatch) -> None:
    """The developer's own MEDIA_HYGIENE_DEBUG does not leak into these tests."""
    monkeypatch.delenv(DEBUG_VARIABLE, raising=False)
    monkeypatch.setattr(sys, "argv", ["media-hygiene"])


def test_ctrl_c_inside_a_task_group_is_a_stop() -> None:
    """The interrupted code, one calm line, no "Unexpected error"."""
    result = CliRunner().invoke(_group_app(), ["inventory"])
    assert result.exit_code == ExitCode.INTERRUPTED
    assert "Unexpected error" not in result.output
    assert "Traceback" not in result.output


def test_a_bug_inside_a_task_group_names_the_real_error() -> None:
    """The report says what failed, not "unhandled errors in a TaskGroup"."""
    result = CliRunner().invoke(_group_app(), ["clean"])
    assert result.exit_code == ExitCode.FAILURE
    flat = " ".join(result.output.split())
    assert "OSError: disk gone" in flat
    assert "ExceptionGroup" not in flat
