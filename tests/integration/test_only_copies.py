"""The files set aside that exist nowhere else (0688), on the demo tree.

An exact copy set aside has its kept twin: 0 only copy. A near duplicate set aside
names a keeper of other content: 1 only copy each. `purge` lists them and asks apart.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import journal_file
from media_hygiene.actions.runs import list_run_ids
from media_hygiene.console.output import Output
from media_hygiene.services.only_copies import only_copies
from media_hygiene.services.only_count import only_count
from tests.support.cli import run

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

WHATSAPP = "IMG-20210705-WA0001.jpg"
EMAIL = "Plage (petite).jpg"


def _only(locations: Locations) -> list[str]:
    """The names of the only copies of every run in the quarantine.

    Args:
        locations: The mount points.

    Returns:
        Their file names, sorted.
    """
    runs = list_run_ids(locations.journal_dir)
    found = only_copies((locations.quarantine_dir,), locations.journal_dir, runs)
    assert found.size == sum(file.stat().st_size for file in found.files)
    return sorted(file.name for file in found.files)


def _counted(locations: Locations) -> int | None:
    """The home page's count of the only copies, from the index.

    Args:
        locations: The mount points.

    Returns:
        It.
    """
    runs = list_run_ids(locations.journal_dir)
    return only_count(locations.index_file, locations.journal_dir, runs)


def test_exact_copies_are_covered(cli: CliRunner, locations: Locations) -> None:
    """A plain clean sets aside exact copies only: none is an only copy."""
    assert run(cli, "clean", "--yes").exit_code == 0
    set_aside = {p.name for p in locations.quarantine_dir.rglob("*") if p.is_file()}
    only = _only(locations)
    assert "IMG_0001_interrupted.jpg" in only  # unreadable: set aside, no twin
    assert len(only) < len(set_aside)  # the exact copies are covered
    assert _counted(locations) == len(only)  # the home page's count agrees


def test_near_duplicates_are_only_copies(cli: CliRunner, locations: Locations) -> None:
    """The near duplicates set aside are counted, one each."""
    assert run(cli, "clean", "--yes", "--tier", "near-all").exit_code == 0
    only = _only(locations)
    assert WHATSAPP in only
    assert EMAIL in only
    assert _counted(locations) == len(only)


def test_a_keeper_gone_uncovers_its_copy(cli: CliRunner, locations: Locations) -> None:
    """The kept twin deleted by hand: its copy in the quarantine is the only one."""
    assert run(cli, "clean", "--yes").exit_code == 0
    run_id = list_run_ids(locations.journal_dir)[0]
    keeper = next(
        line.split('"keeper":"')[1].split('"')[0]
        for line in journal_file(locations.journal_dir, run_id).read_text().splitlines()
        if '"keeper":"' in line
    )
    before = _counted(locations)
    Path(keeper).unlink()
    assert len(_only(locations)) >= 1
    # The home page trusts the index until the next audit; `purge` asks the disk.
    assert _counted(locations) == before
    assert run(cli, "audit").exit_code == 0
    assert _counted(locations) == len(_only(locations))


def test_a_run_without_journal_counts_every_file(
    cli: CliRunner, locations: Locations
) -> None:
    """No journal, no proof of a twin: every file of its folder counts."""
    assert run(cli, "clean", "--yes").exit_code == 0
    run_id = list_run_ids(locations.journal_dir)[0]
    journal_file(locations.journal_dir, run_id).unlink()
    found = only_copies((locations.quarantine_dir,), locations.journal_dir, [run_id])
    held = [p for p in (locations.quarantine_dir / run_id).rglob("*") if p.is_file()]
    assert len(found.files) == len(held)


def test_purge_lists_them_and_asks_apart(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Yes to the purge, no to the only copies: nothing is erased."""
    assert run(cli, "clean", "--yes", "--tier", "near-all").exit_code == 0
    answers = iter((True, False))
    asked: list[str] = []

    def answer(_output: Output, question: str) -> bool:
        asked.append(question)
        return next(answers)

    monkeypatch.setattr(Output, "confirm", answer)
    text = " ".join(run(cli, "purge").output.split())
    assert "exist nowhere else" in text
    assert WHATSAPP in text
    assert "only copies too?" in asked[1]
    assert "Nothing was changed." in text
    assert list(locations.quarantine_dir.rglob(WHATSAPP))
