"""Ctrl+C after a command ended: its own code, never a traceback (TODO 0275)."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from contextlib import nullcontext
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.teardown import QuietEnd, exit_code, quiet_teardown

if TYPE_CHECKING:
    from collections.abc import Callable

# A page's last request still running in asyncio's executor when the command ends.
_BUSY_AT_EXIT: Final = """
import asyncio, sys, threading
from media_hygiene.teardown import quiet_teardown

never = threading.Event()

async def page():
    asyncio.get_running_loop().run_in_executor(None, never.wait, 60)
    await asyncio.sleep(0)

try:
    with quiet_teardown():
        loop = asyncio.new_event_loop()
        loop.run_until_complete(page())
        print("Home page closed.", flush=True)
        raise SystemExit(3)
finally:
    print("armed", flush=True)
"""
_CODE: Final = 3
_WAIT_S: Final = 20


def test_ctrl_c_while_a_thread_ends_prints_no_traceback() -> None:
    """Two Ctrl+C while a worker is still busy: the command's code, a clean stderr."""
    with subprocess.Popen(  # noqa: S603 - the test's own interpreter and script
        [sys.executable, "-c", _BUSY_AT_EXIT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) as process:
        assert process.stdout is not None
        lines = [process.stdout.readline(), process.stdout.readline()]
        for _ in range(2):
            try:
                process.send_signal(signal.SIGINT)
            except ProcessLookupError:
                break
        out, err = process.communicate(timeout=_WAIT_S)
    assert lines == ["Home page closed.\n", "armed\n"]
    assert not out
    assert not err
    assert process.returncode == _CODE


@pytest.mark.parametrize(
    ("code", "expected"), [(None, 0), (0, 0), (130, 130), ("Bad usage", 1)]
)
def test_exit_code_reads_system_exit_like_the_interpreter(
    code: object, expected: int
) -> None:
    """None is success, a number is itself, a message is a failure."""
    assert exit_code(code) == expected


def test_quiet_end_flushes_then_exits_with_its_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The handler never returns into the interpreter's thread join."""
    ended: list[int] = []
    monkeypatch.setattr(os, "_exit", ended.append)
    QuietEnd(7)(signal.SIGINT, None)
    assert ended == [7]


def _armed(monkeypatch: pytest.MonkeyPatch) -> dict[int, object]:
    """Record the handlers installed instead of installing them.

    Args:
        monkeypatch: Pytest's monkeypatch.

    Returns:
        Signal number → handler, filled as `arm` runs.
    """
    installed: dict[int, object] = {}

    def record(number: int, handler: object) -> None:
        installed[number] = handler

    monkeypatch.setattr(signal, "signal", record)
    return installed


def _codes(installed: dict[int, object]) -> set[int]:
    """The codes the recorded handlers end with.

    Args:
        installed: Signal number → handler.

    Returns:
        Each handler's code.
    """
    assert set(installed) == {signal.SIGINT, signal.SIGTERM}
    return {
        handler.code for handler in installed.values() if isinstance(handler, QuietEnd)
    }


def _raise_exit() -> None:
    raise SystemExit(2)


def _raise_bug() -> None:
    raise RuntimeError


def _return() -> None:
    return


@pytest.mark.parametrize(
    ("command", "code"), [(_raise_exit, 2), (_raise_bug, 1), (_return, 0)]
)
def test_teardown_arms_with_how_the_command_ended(
    monkeypatch: pytest.MonkeyPatch, command: Callable[[], None], code: int
) -> None:
    """Exit, bug or plain return: Ctrl+C and `docker stop` then end with that code."""
    installed = _armed(monkeypatch)
    ending = pytest.raises((SystemExit, RuntimeError)) if code else nullcontext()
    with ending, quiet_teardown():
        command()
    assert _codes(installed) == {code}
