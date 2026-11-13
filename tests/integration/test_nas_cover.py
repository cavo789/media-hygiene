"""A NAS copy counts as cover of a file set aside, until a push moves it (0781).

The closing run of a push keeps the target's listing (`nas_cover`); here it is
written as that run writes it, from the demo tree's files before or after a clean.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.runs import list_run_ids
from media_hygiene.plan.push_entries import Stat
from media_hygiene.services.nas_cover import Listing, cover_file, keep_cover
from media_hygiene.services.only_copies import only_copies
from media_hygiene.services.only_count import only_count
from media_hygiene.services.safety_cache import SlowAsk, safety_key
from tests.support.cli import run
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

WHATSAPP = "IMG-20210705-WA0001.jpg"
TARGET = "\\\\nas\\photos"


def _pushed(locations: Locations, target: str = TARGET) -> None:
    """Keep the listing a proven push of the photos as they are now would keep."""
    files = {
        str(path): Stat(path.stat().st_size, path.stat().st_mtime_ns)
        for path in locations.data_dir.rglob("*")
        if path.is_file()
    }
    keep_cover(locations.journal_dir, Listing("20261113-090000", target, files))


def _names(locations: Locations) -> tuple[list[str], int]:
    """The only copies by name, and how many exist only on the NAS."""
    runs = list_run_ids(locations.journal_dir)
    found = only_copies((locations.quarantine_dir,), locations.journal_dir, runs)
    return sorted(file.name for file in found.files), found.nas


def _counted(locations: Locations) -> tuple[int, int]:
    """The home page's counts, from the index: nowhere else, only on the NAS."""
    runs = list_run_ids(locations.journal_dir)
    counted = only_count(locations.index_file, locations.journal_dir, runs)
    assert counted is not None
    return counted.only, counted.nas


def test_pushed_then_set_aside_is_covered(cli: CliRunner, locations: Locations) -> None:
    """A near duplicate pushed before it was set aside: only on the NAS, said apart."""
    _pushed(locations)
    assert run(cli, "clean", "--yes", "--tier", "near-all").exit_code == 0
    names, nas = _names(locations)
    assert WHATSAPP not in names
    assert nas >= 1
    assert _counted(locations) == (len(names), nas)


def test_set_aside_before_any_push_is_an_only_copy(
    cli: CliRunner, locations: Locations
) -> None:
    """No push, or a push after the clean: the file was not on the NAS."""
    assert run(cli, "clean", "--yes", "--tier", "near-all").exit_code == 0
    names, nas = _names(locations)
    assert WHATSAPP in names
    assert nas == 0
    _pushed(locations)  # the photos without what was set aside
    assert _names(locations) == (names, 0)


def test_a_new_push_or_another_target_uncovers_it(
    cli: CliRunner, locations: Locations
) -> None:
    """The next push moves the copy into `.removed`; `--to` elsewhere: not there."""
    _pushed(locations)
    assert run(cli, "clean", "--yes", "--tier", "near-all").exit_code == 0
    covered = _names(locations)
    _pushed(locations)  # the next push: the copy left for `.removed`
    names, nas = _names(locations)
    assert WHATSAPP in names
    assert nas == 0
    assert len(names) == len(covered[0]) + covered[1]
    _pushed(locations, "E:\\Other")  # another target: holds nothing set aside
    assert _names(locations) == (names, 0)


def test_purge_or_undo_takes_it_out(cli: CliRunner, locations: Locations) -> None:
    """Out of the quarantine, a file asks for no cover."""
    _pushed(locations)
    assert run(cli, "clean", "--yes", "--tier", "near-all").exit_code == 0
    assert run(cli, "undo", "--yes").exit_code == 0
    assert _names(locations) == ([], 0)
    _pushed(locations)
    assert run(cli, "clean", "--yes", "--tier", "near-all").exit_code == 0
    assert run(cli, "purge", "--yes").exit_code == 0
    assert _names(locations) == ([], 0)


def test_the_card_cache_sees_a_new_push(cli: CliRunner, locations: Locations) -> None:
    """The home card's key changes when a push keeps another listing."""
    assert run(cli, "clean", "--yes", "--tier", "near-all").exit_code == 0
    runtime = make_runtime(locations)
    ask = SlowAsk(runtime, tuple(list_run_ids(locations.journal_dir)), ())
    before = safety_key(ask)
    _pushed(locations)
    assert safety_key(ask) != before
    assert Path(cover_file(locations.journal_dir)).is_file()
