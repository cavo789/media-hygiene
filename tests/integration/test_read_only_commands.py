"""The promise of the help: every read-only command runs on read-only photos, unchanged.

The data tree is made read-only (as `:ro` would), then each command of
`READ_ONLY_COMMANDS` runs: none may fail for lack of write access, none may change a
byte. A command added to the list without a run here fails the first test.
"""

from __future__ import annotations

import os
import re
from typing import TYPE_CHECKING

import pytest

from media_hygiene.cli.app import build_app
from media_hygiene.cli.safety import READ_ONLY_COMMANDS, read_only_marker
from media_hygiene.services import places as places_service
from media_hygiene.services import reviewing, sort_reviewing
from tests.integration.test_clean_undo import manifest
from tests.support.cli import run

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

PORT = 8765
# Each read-only command, in an order where each finds what it needs.
RUNS: tuple[tuple[str, ...], ...] = (
    ("audit",),
    ("crosscheck",),
    ("classify",),
    ("review-sort",),
    ("review",),
    ("places",),
    ("inventory",),
    ("history",),
    ("reports",),
    ("config",),
)


def test_the_help_marks_exactly_the_commands_run_here() -> None:
    """The marker, the list in the code and the runs below are one list."""
    app = build_app()
    marked = {
        info.name
        for info in app.registered_commands
        if (info.help or "").startswith(read_only_marker())
    }
    assert marked == READ_ONLY_COMMANDS == {args[0] for args in RUNS}


def ready_then_stop(*_args: object) -> Callable[..., object]:
    """A server that says it is ready, then gets Ctrl+C."""

    async def serve(_app: object, _port: int, ready: Callable[[int], None]) -> None:
        ready(PORT)
        raise KeyboardInterrupt

    return serve


@pytest.fixture
def read_only_data(locations: Locations) -> Iterator[Path]:
    """The demo tree, every folder and file read-only, as `:ro` would make it."""
    data = locations.data_dir
    paths = sorted(data.rglob("*"), reverse=True)
    for path in (*paths, data):
        path.chmod(0o555 if path.is_dir() else 0o444)
    yield data
    for path in (data, *sorted(data.rglob("*"))):
        path.chmod(0o755 if path.is_dir() else 0o644)


def test_read_only_commands_change_nothing_in_the_photos(
    cli: CliRunner, read_only_data: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each one runs on read-only folders and leaves every byte and date as it was."""
    if os.geteuid() == 0:  # pragma: no cover - root ignores file permissions
        pytest.skip("root can write to read-only folders")
    for module in (reviewing, sort_reviewing, places_service):
        monkeypatch.setattr(module, "run_server", ready_then_stop())
    before = manifest(read_only_data)
    for args in RUNS:
        result = run(cli, *args)
        assert "Permission denied" not in result.output, args
        assert not re.search(r"Traceback", result.output), args
        assert manifest(read_only_data) == before, args
        # crosscheck stops early here: no Czkawka results to compare with.
        assert result.exit_code == (args[0] == "crosscheck"), result.output
    audit = run(cli, "audit").output
    assert "🔒 Read-only: your photos and videos are not touched." in audit
    assert "Add :ro" in audit  # a permission is no `:ro` mount: the tip says how
