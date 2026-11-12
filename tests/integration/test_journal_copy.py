"""Each run's journal copied as `<run>.jsonl` beside its quarantine folder (0697).

The copy travels with the files set aside: `/journal` wiped, `undo` takes it back and
restores every byte. It is never inside the run's folder, never taken for a run or a
file set aside; a partial undo refreshes it, a whole one and `purge` erase it, and a
drive's own quarantine (`/quarantine/d`) holds its own.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.journal import journal_file, read_journal
from media_hygiene.actions.journal_copy import journal_copy
from media_hygiene.actions.purge import quarantine_runs
from media_hygiene.actions.undo_pick import RunPick
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.only_copies import only_copies
from media_hygiene.services.undo import undo_pick
from media_hygiene.services.undo_orphan import orphan_plan
from tests.integration.test_clean_undo import manifest
from tests.integration.test_quarantine_drives import clean, digests, mount, remount
from tests.support.cli import run
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def test_clean_writes_it_beside_and_readers_ignore_it(
    cli: CliRunner, locations: Locations
) -> None:
    """Same bytes as the journal, beside the run's folder; no reader counts it."""
    run_id = clean(cli, locations)
    copy = journal_copy(locations.quarantine_dir, run_id)
    journal = journal_file(locations.journal_dir, run_id)
    assert copy.read_bytes() == journal.read_bytes()
    assert copy.parent == locations.quarantine_dir  # beside, never inside
    assert not list((locations.quarantine_dir / run_id).rglob("*.jsonl"))
    assert not list(locations.quarantine_dir.glob(".*.tmp"))  # atomic, no draft left
    assert quarantine_runs(locations.quarantine_dir) == [run_id]
    held = only_copies((locations.quarantine_dir,), locations.journal_dir, [run_id])
    assert copy not in held.files
    journal.unlink()  # `undo --from-quarantine` reads the run's folder only
    moves = orphan_plan(make_runtime(locations), run_id).moves
    assert moves
    assert all(move.quarantined != copy for move in moves)


def test_journal_wiped_undo_takes_the_copy_back(
    cli: CliRunner, locations: Locations
) -> None:
    """`/journal` emptied by hand: `undo` restores every file from the copy."""
    before = manifest(locations.data_dir)
    run_id = clean(cli, locations)
    journal = journal_file(locations.journal_dir, run_id)
    journal.unlink()
    result = run(cli, "undo", "--yes")
    assert result.exit_code == 0, result.output
    assert "taken back from its quarantine" in " ".join(result.output.split())
    assert journal.is_file()
    assert manifest(locations.data_dir) == before
    assert not (locations.quarantine_dir / run_id).exists()
    assert not journal_copy(locations.quarantine_dir, run_id).exists()  # all back


def test_never_over_a_journal(cli: CliRunner, locations: Locations) -> None:
    """A copy that differs never replaces the journal in `/journal`."""
    run_id = clean(cli, locations)
    journal = journal_file(locations.journal_dir, run_id)
    copy = journal_copy(locations.quarantine_dir, run_id)
    copy.write_text("not a journal\n", encoding="utf-8")
    assert run(cli, "undo", "--yes").exit_code == 0
    assert journal.read_text(encoding="utf-8").startswith("{")


def test_a_partial_undo_refreshes_it(cli: CliRunner, locations: Locations) -> None:
    """After an undo of one file, the copy says it came back."""
    run_id = clean(cli, locations)
    journal = journal_file(locations.journal_dir, run_id)
    aside = [entry.seq for entry in read_journal(journal) if entry.quarantine]
    assert len(aside) > 1
    pick = RunPick(run_id, frozenset(aside[:1]))
    undo_pick(make_runtime(locations), pick, NullProgress())
    copy = journal_copy(locations.quarantine_dir, run_id)
    assert (locations.quarantine_dir / run_id).is_dir()  # the others stay aside
    assert copy.read_bytes() == journal.read_bytes()
    assert '"phase":"undo"' in copy.read_text(encoding="utf-8")


def test_purge_removes_it_with_the_run(cli: CliRunner, locations: Locations) -> None:
    """`purge <run>`: the run's folder and the copy beside it go together."""
    run_id = clean(cli, locations)
    assert run(cli, "purge", run_id, "--yes").exit_code == 0
    assert not (locations.quarantine_dir / run_id).exists()
    assert not journal_copy(locations.quarantine_dir, run_id).exists()


def test_a_drive_quarantine_holds_its_own(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D:'s quarantine gets a copy too; wiped journal, undo; purge erases both."""
    own = mount(locations, monkeypatch, d_quarantine=True)
    before = digests(locations.data_dir)
    run_id = clean(cli, locations)
    journal = journal_file(locations.journal_dir, run_id)
    copies = [
        journal_copy(folder, run_id) for folder in (locations.quarantine_dir, own)
    ]
    held = [c for c in copies if (c.parent / run_id).is_dir()]
    assert held
    assert all(copy.read_bytes() == journal.read_bytes() for copy in held)
    assert quarantine_runs(own) == [run_id] or not (own / run_id).exists()
    journal.unlink()
    assert run(cli, "undo", "--yes").exit_code == 0
    assert digests(locations.data_dir) == before
    assert not any(copy.exists() for copy in copies)


def test_history_lists_a_run_known_only_from_its_copy(
    cli: CliRunner, locations: Locations
) -> None:
    """`/journal` emptied: `mh history` still shows the run, marked (0721)."""
    run_id = clean(cli, locations)
    journal_file(locations.journal_dir, run_id).unlink()
    history = " ".join(run(cli, "history").output.split())
    assert run_id in history
    assert "(from the quarantine)" in history
    assert "takes that copy back first" in history
    assert not journal_file(locations.journal_dir, run_id).exists()  # read-only
    assert run(cli, "undo", run_id, "--yes").exit_code == 0
    assert "from the quarantine" not in " ".join(run(cli, "history").output.split())


def test_journal_lost_and_drive_back_under_another_letter(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D: back as E:, `/journal` wiped: the copy found, every byte back (0774)."""
    mount(locations, monkeypatch, d_quarantine=True)
    before = digests(locations.data_dir / "d")
    run_id = clean(cli, locations)
    remount(locations, monkeypatch, ("e",))
    journal = journal_file(locations.journal_dir, run_id)
    journal.unlink()
    assert run_id in run(cli, "history").output  # listed from the quarantine
    result = run(cli, "undo", run_id, "--yes")
    assert result.exit_code == 0, result.output
    text = " ".join(result.output.split())
    assert "taken back from its quarantine" in text
    assert f"Run {run_id} found in the quarantine of E:, not of D:." in text
    assert digests(locations.data_dir / "e") == before
    assert not (locations.quarantine_dir / "e" / run_id).exists()
