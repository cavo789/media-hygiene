"""Apply all (0522): the choices of two pages, one `clean --decisions`, one undo."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from media_hygiene.cli.home_pending import home_pending
from media_hygiene.cli.menu_steps import full_catalog
from tests.integration.test_unwanted_review import (
    NIGHT,
    SCREENSHOT,
    add_unwanted,
    junk_session,
    rank_of,
)
from tests.support.cli import run
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def _set_aside_in_search(locations: Locations) -> None:
    """The screenshot set aside in `library`, beside the junk review's choice."""
    file = locations.reports_dir / "decisions.json"
    shot = locations.data_dir / SCREENSHOT
    said = json.loads(file.read_text("utf-8"))
    host = make_runtime(locations).mapper.to_host(shot)
    stat = shot.stat()
    said["chosen"] = [
        {"path": host, "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
    ]
    file.write_text(json.dumps(said), "utf-8")


def test_two_pages_applied_at_once_read_zero_and_undone_at_once(
    cli: CliRunner, locations: Locations
) -> None:
    """One click: both files go, the count reads 0 from disk, one undo restores both."""
    data = locations.data_dir
    add_unwanted(data)
    session = junk_session(locations)
    session.decide({rank_of(session, "night.jpg"): True})
    _set_aside_in_search(locations)
    pending = home_pending(locations.reports_dir)
    assert pending is not None
    assert pending.total == 2
    assert len(pending.pages) == 2
    [apply] = [step for step in full_catalog().steps if step.name == "apply"]
    words = apply.words({})
    assert words[-1] == "--decisions"  # alone: decisions.json, every page's
    result = run(cli, *words, "decisions.json", "--yes")
    assert result.exit_code == 0, result.output
    assert not (data / NIGHT).exists()
    assert not (data / SCREENSHOT).exists()
    assert home_pending(locations.reports_dir) is None
    assert run(cli, "undo").exit_code == 0
    assert (data / NIGHT).is_file()
    assert (data / SCREENSHOT).is_file()
