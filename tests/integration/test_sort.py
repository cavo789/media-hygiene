"""`sort` applies the edited workbook, proves nothing was lost; `undo` reverses it."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import journal_file, read_journal
from media_hygiene.actions.kinds import ActionKind, Phase
from media_hygiene.classify.models import Band, SortReason
from media_hygiene.constants import MediaKind
from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan.models import MediaFile
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.classify import ClassifyService
from tests.support.runtime import make_runtime
from tests.support.sorting import (
    EVENT_NAME,
    MIXED,
    PARTY,
    WEDDING,
    build_library,
    classify,
    folders,
    name_first_event,
    snapshot,
    sort,
    undo,
)

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def test_classify_edit_sort_then_undo_gives_the_tree_back(locations: Locations) -> None:
    """Moves as edited, nothing lost, then byte-identical after undo, folders back."""
    data = locations.data_dir
    build_library(data)
    runtime = make_runtime(locations)
    AuditService(runtime, NullProgress()).run()
    start, tree = snapshot(data), folders(data)
    workbook = classify(runtime)
    name_first_event(workbook)
    result = sort(runtime)
    assert result.manifest.intact, result.manifest
    assert not result.moves.outcome.failed
    assert (data / "c/2016" / EVENT_NAME / "IMG_0000.jpg").is_file()
    assert (data / "c/2018/Mariage/DSC_0000.xmp").is_file()  # the sidecar followed
    assert not (data / PARTY).exists()  # Thumbs.db quarantined, folder removed
    assert not (data / WEDDING).exists()  # desktop.ini too
    assert (data / MIXED / "notes.txt").is_file()  # a folder holding more stays
    assert result.folders.removed >= 2
    assert isinstance(result.manifest_file, Path)
    manifest = json.loads(result.manifest_file.read_text("utf-8"))
    assert manifest["before"] == manifest["after"]
    outcome = undo(runtime, result.run_id)
    assert not outcome.failed, outcome
    assert not outcome.skipped, outcome
    assert snapshot(data) == start
    assert folders(data) == tree


def test_the_index_follows_the_moves_and_undo(locations: Locations) -> None:
    """A moved file keeps its digest: the next audit hashes nothing again."""
    build_library(locations.data_dir)
    runtime = make_runtime(locations)
    AuditService(runtime, NullProgress()).run()
    name_first_event(classify(runtime))
    result = sort(runtime)
    moved = next(e for e in result.moves.moved if e.path.endswith("IMG_0000.jpg"))
    stat = (moved.size, moved.mtime_ns, MediaKind.IMAGE)
    with FactsRepository.open(runtime.index_file) as index:
        assert index.get(MediaFile(Path(moved.target or ""), *stat)).integrity
        assert not index.get(MediaFile(Path(moved.path), *stat)).integrity
    undo(runtime, result.run_id)
    with FactsRepository.open(runtime.index_file) as index:
        assert index.get(MediaFile(Path(moved.path), *stat)).integrity


def test_classify_right_after_sort_proposes_nothing_to_move(
    locations: Locations,
) -> None:
    """In place: every file already sits where the plan puts it."""
    build_library(locations.data_dir)
    runtime = make_runtime(locations)
    name_first_event(classify(runtime))
    sort(runtime)
    proposals = ClassifyService(runtime, NullProgress()).run().classification.proposals
    moving = [p.file.path for p in proposals if not p.in_place]
    assert not moving


def test_an_unedited_sort_then_classify_proposes_nothing_to_move(
    cli: CliRunner, locations: Locations
) -> None:
    """Every band, "to check" included: the guesses sorted stay where they are."""
    assert cli is not None  # the demo tree, in the data folder
    runtime = make_runtime(locations)
    classify(runtime)
    unsure = [
        p
        for p in ClassifyService(runtime, NullProgress()).run().classification.proposals
        if p.band is Band.UNSURE and not p.in_place
    ]
    assert unsure  # the demo tree has guesses to check
    assert not sort(runtime).moves.outcome.failed
    proposals = ClassifyService(runtime, NullProgress()).run().classification.proposals
    assert not [p.file.path for p in proposals if not p.in_place]
    kept = [p for p in proposals if p.reason is SortReason.PREVIOUS_GUESS]
    assert len(kept) == len(unsure)


def test_the_journal_names_the_plan_and_each_row(locations: Locations) -> None:
    """A resumed run finds the rows of its plan in the journal."""
    build_library(locations.data_dir)
    runtime = make_runtime(locations)
    name_first_event(classify(runtime))
    result = sort(runtime)
    entries = read_journal(journal_file(locations.journal_dir, result.run_id))
    moves = [
        e for e in entries if e.action is ActionKind.MOVE and e.phase is Phase.SORT
    ]
    assert {e.plan for e in moves} == {result.manifest.plan_id}
    assert all(e.row for e in moves if not e.path.endswith(".xmp"))
