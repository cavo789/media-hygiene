"""The way back survives a lost journal (0687): saved by `backup`, or rebuilt.

`backup` archives every journal and the choice files; `restore` puts back those
missing, never over one there. Without any journal, `undo --from-quarantine` rebuilds
the moves from the quarantine's mirror layout.
"""

from __future__ import annotations

import hashlib
import shutil
import sqlite3
from typing import TYPE_CHECKING

import pytest

from media_hygiene.actions.journal import journal_file
from media_hygiene.errors import JournalError
from media_hygiene.index.schema import prepare
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.backup_extra import JOURNAL_PREFIX, REPORTS_PREFIX
from media_hygiene.services.cache_backup import make_backup
from media_hygiene.services.cache_restore import RestoreRequest, restore_backup
from media_hygiene.services.undo import undo_run
from media_hygiene.services.undo_orphan import apply_orphan_plan, orphan_plan
from tests.integration.test_clean_undo import Manifest, clean, manifest
from tests.support.demo import build_demo
from tests.support.runtime import make_runtime

_EMPTY = hashlib.sha256(b"").hexdigest()

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime


def _cleaned(locations: Locations, *, delete: bool = False) -> tuple[Runtime, str]:
    """The demo tree (built already) cleaned, with an index to back up.

    Args:
        locations: The mount points.
        delete: `clean --delete`.

    Returns:
        The runtime and the run.
    """
    runtime = make_runtime(locations)
    run_id = clean(runtime, delete=delete)
    if not locations.index_file.is_file():
        connection = sqlite3.connect(locations.index_file)
        prepare(connection)
        connection.close()
    return runtime, run_id


def _but_deleted(after: Manifest, before: Manifest) -> bool:
    """Tell whether the tree is back whole but for the files a clean deletes.

    An empty file is deleted, not set aside (only a journal names it): it is the one
    thing the quarantine's layout cannot give back.

    Args:
        after: The tree after the rebuild.
        before: The tree before the clean.

    Returns:
        True when every file present matches, and only empty ones are missing.
    """
    missing = set(before) - set(after)
    return all(after[name] == before[name] for name in after) and all(
        before[name][0] == _EMPTY for name in missing
    )


@pytest.mark.parametrize("delete", [False, True])
def test_backup_wipe_restore_undo(locations: Locations, *, delete: bool) -> None:
    """A clean, its journal lost then restored: undo gives the disk back whole."""
    build_demo(locations.data_dir)
    before = manifest(locations.data_dir)
    runtime, run_id = _cleaned(locations, delete=delete)
    choices = locations.reports_dir / "decisions.json"
    choices.write_text('{"pairs": {}}', encoding="utf-8")
    backup = make_backup(runtime)
    assert JOURNAL_PREFIX + f"{run_id}.jsonl" in backup.manifest.members
    assert REPORTS_PREFIX + "decisions.json" in backup.manifest.members
    shutil.rmtree(locations.journal_dir)
    locations.journal_dir.mkdir()
    choices.unlink()
    restored = restore_backup(runtime, RestoreRequest(backup.path.name))
    assert JOURNAL_PREFIX + f"{run_id}.jsonl" in restored.missing
    assert choices.read_text(encoding="utf-8") == '{"pairs": {}}'
    outcome = undo_run(runtime, run_id, NullProgress())
    assert not outcome.failed
    assert manifest(locations.data_dir) == before


def test_restore_never_writes_over_a_journal(locations: Locations) -> None:
    """A journal on the disk is as new as the archive's, or newer: left untouched."""
    build_demo(locations.data_dir)
    runtime, run_id = _cleaned(locations)
    backup = make_backup(runtime)
    file = journal_file(locations.journal_dir, run_id)
    newer = file.read_bytes() + b"\n"
    file.write_bytes(newer)
    restored = restore_backup(runtime, RestoreRequest(backup.path.name))
    assert not restored.missing
    assert file.read_bytes() == newer


def test_undo_from_quarantine_without_journal(locations: Locations) -> None:
    """Every quarantined file back at its place, proven; the run's folder gone."""
    build_demo(locations.data_dir)
    before = manifest(locations.data_dir)
    runtime = make_runtime(locations)
    run_id = clean(runtime)
    journal_file(locations.journal_dir, run_id).unlink()
    plan = orphan_plan(runtime, run_id)
    assert plan.moves
    assert not plan.left
    outcome = apply_orphan_plan(plan)
    assert len(outcome.back) == len(plan.moves)
    assert not outcome.left
    assert _but_deleted(manifest(locations.data_dir), before)
    assert not (locations.quarantine_dir / run_id).exists()


def test_undo_from_quarantine_never_over_a_file(locations: Locations) -> None:
    """A file at the place already: it stays in the quarantine, untouched."""
    build_demo(locations.data_dir)
    runtime = make_runtime(locations)
    run_id = clean(runtime)
    journal_file(locations.journal_dir, run_id).unlink()
    first = orphan_plan(runtime, run_id).moves[0]
    first.original.write_bytes(b"new")
    plan = orphan_plan(runtime, run_id)
    assert first.quarantined in dict(plan.left)
    apply_orphan_plan(plan)
    assert first.original.read_bytes() == b"new"
    assert first.quarantined.is_file()


def test_undo_from_quarantine_drive_changed_letter(locations: Locations) -> None:
    """The photos' drive mounted under another letter: nothing moves, all said."""
    build_demo(locations.data_dir)
    runtime = make_runtime(locations)
    run_id = clean(runtime)
    journal_file(locations.journal_dir, run_id).unlink()
    (locations.data_dir / "c").rename(locations.data_dir / "e")
    plan = orphan_plan(runtime, run_id)
    gone = locations.data_dir / "c"
    assert not any(move.original.is_relative_to(gone) for move in plan.moves)
    assert any("/c/" in str(file) for file, _why in plan.left)


def test_quarantine_moved_to_a_drive_quarantine(locations: Locations) -> None:
    """The run's folder moved to another quarantine folder: its layout still reads."""
    build_demo(locations.data_dir)
    before = manifest(locations.data_dir)
    runtime = make_runtime(locations)
    run_id = clean(runtime)
    journal_file(locations.journal_dir, run_id).unlink()
    elsewhere = locations.quarantine_dir.parent / "quarantine-moved"
    (locations.quarantine_dir).rename(elsewhere)
    moved = make_runtime(locations.model_copy(update={"quarantine_dir": elsewhere}))
    apply_orphan_plan(orphan_plan(moved, run_id))
    assert _but_deleted(manifest(locations.data_dir), before)


def test_undo_from_quarantine_refused_with_a_journal(locations: Locations) -> None:
    """The journal is there: plain undo is exact, the rebuild is refused."""
    build_demo(locations.data_dir)
    runtime = make_runtime(locations)
    run_id = clean(runtime)
    with pytest.raises(JournalError):
        orphan_plan(runtime, run_id)
