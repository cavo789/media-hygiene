"""Apply all (0522): the choices of two pages, one `clean --decisions`, one undo."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.home_pending import home_pending
from media_hygiene.cli.menu_steps import full_catalog
from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.report.chosen_decisions import PEOPLE_FOUND_BY
from media_hygiene.search.chosen import Selection
from media_hygiene.services.chosen_place import chosen_store
from media_hygiene.services.intruder_pick import FOUND_BY
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
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


_MOVED: Final = ("night", "intruder", "person")


def _versions(path: Path) -> tuple[PhotoVersion, ...]:
    """The file as it is now."""
    stat = path.stat()
    return (PhotoVersion(path, stat.st_size, stat.st_mtime_ns),)


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


def test_intruders_and_people_applied_and_undone_with_the_rest(
    cli: CliRunner, locations: Locations
) -> None:
    """Junk, an intruder, a person's photo: one count from disk, one run, one undo."""
    data = locations.data_dir
    add_unwanted(data)
    session = junk_session(locations)
    session.decide({rank_of(session, "night.jpg"): True})
    intruder = data / "notes.zip"
    intruder.write_bytes(b"not a photo")
    runtime = make_runtime(locations)
    said = chosen_store(runtime).add(Selection(_versions(intruder), FOUND_BY))
    assert said
    person = data / SCREENSHOT
    chosen_store(runtime).add(Selection(_versions(person), f"{PEOPLE_FOUND_BY}Ex"))
    pending = home_pending(locations.reports_dir)
    assert pending is not None
    assert pending.total == len(_MOVED)
    assert {page.label for page in pending.pages} >= {"Intruder files", "People"}
    [apply] = [step for step in full_catalog().steps if step.name == "apply"]
    result = run(cli, *apply.words({}), "decisions.json", "--yes")
    assert result.exit_code == 0, result.output
    moved = (data / NIGHT, intruder, person)
    assert not any(path.exists() for path in moved)
    assert home_pending(locations.reports_dir) is None
    assert run(cli, "undo").exit_code == 0
    assert all(path.is_file() for path in moved)


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
