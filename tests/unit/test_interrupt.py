"""Ctrl+C: one calm line and the code 130, workers stopped at once, asyncio quiet."""

from __future__ import annotations

import io
import logging
import time

import pytest
import typer
from rich.console import Console
from typer.testing import CliRunner

from media_hygiene.cli.localized import LocalizedGroup
from media_hygiene.console.logs import configure_logging
from media_hygiene.constants import ExitCode, Verbosity
from media_hygiene.services.runtime import process_pool

_TRACEBACK = "Traceback"
_DECODE_SECONDS = 60
_PATIENCE_SECONDS = 30


def _interrupt_a_long_decode() -> None:
    """Press Ctrl+C while a worker is busy for a minute.

    Raises:
        KeyboardInterrupt: Always, as the terminal would.
    """
    with process_pool() as pool:
        pool.submit(time.sleep, _DECODE_SECONDS)
        raise KeyboardInterrupt


def _interrupted_app() -> typer.Typer:
    """An app whose two commands are stopped by Ctrl+C, one of them read-only.

    Returns:
        The app, built with the root group of the real CLI.
    """
    app = typer.Typer(cls=LocalizedGroup)

    def _pressed() -> None:
        raise KeyboardInterrupt

    app.command(name="audit")(_pressed)
    app.command(name="clean")(_pressed)
    return app


def test_a_read_only_command_says_the_photos_were_not_touched() -> None:
    """Ctrl+C during `audit`: the reassuring line, no traceback, the code 130."""
    result = CliRunner().invoke(_interrupted_app(), ["audit"])
    assert result.exit_code == ExitCode.INTERRUPTED
    assert "Stopped (Ctrl+C). Your photos and videos were not touched." in result.output
    assert _TRACEBACK not in result.output


def test_a_command_that_acts_only_says_it_stopped() -> None:
    """Ctrl+C during `clean`: no promise about the photos, still no traceback."""
    result = CliRunner().invoke(_interrupted_app(), ["clean"])
    assert result.exit_code == ExitCode.INTERRUPTED
    assert "Stopped (Ctrl+C)." in result.output
    assert "not touched" not in result.output
    assert _TRACEBACK not in result.output


def test_the_image_pool_does_not_wait_for_decodes_under_way() -> None:
    """A failed block terminates the workers instead of waiting for their work."""
    started = time.monotonic()
    with pytest.raises(KeyboardInterrupt):
        _interrupt_a_long_decode()
    assert time.monotonic() - started < _PATIENCE_SECONDS


def test_the_image_pool_finishes_its_work_after_a_normal_end() -> None:
    """Without an error, leaving the block still waits for the results."""
    with process_pool() as pool:
        future = pool.submit(abs, -3)
    assert future.result() == abs(-3)


@pytest.mark.parametrize(
    ("verbosity", "level"),
    [(Verbosity.WARNING, logging.CRITICAL), (Verbosity.DEBUG, logging.DEBUG)],
)
def test_asyncio_speaks_only_in_debug(verbosity: Verbosity, level: int) -> None:
    """Asyncio's own warnings and tracebacks are hidden outside debug.

    Args:
        verbosity: The configured verbosity.
        level: The level the asyncio logger then has.
    """
    asyncio_logger = logging.getLogger("asyncio")
    previous = asyncio_logger.level
    try:
        configure_logging(verbosity, Console(file=io.StringIO()))
        assert asyncio_logger.level == level
    finally:
        asyncio_logger.setLevel(previous)
