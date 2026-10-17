"""Folders a clean empties: junk to the quarantine, removed, undo restores (0202)."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, override

import pytest

from media_hygiene.actions.journal import journal_file, read_journal
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.runs import summarize
from media_hygiene.actions.sort_folders import candidates
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import MountTable
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.clean import CleanMode, CleanService
from media_hygiene.services.emptied_folders import base_rules, emptied_by
from media_hygiene.services.undo import undo_run
from tests.support.media import MediaFactory
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.outcome import Outcome
    from media_hygiene.config.layers import Layer
    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime

_PHOTOS = "c/Photos"
_BACKUP = "d/Old disk"
_KEEP: Layer = {"folders": {"preferred": ["C:\\Photos\\Keep"]}}
_THUMBS = b"thumbnail cache"


class _StopAtFirstFile(NullProgress):
    """Ctrl+C right after the first file of the clean."""

    @override
    def advance(self, weight: int = 1) -> None:
        """Press Ctrl+C.

        Args:
            weight: Unused.

        Raises:
            KeyboardInterrupt: Always.
        """
        raise KeyboardInterrupt


def _tree(data: Path) -> None:
    """Kept photos, a folder of copies (and its Thumbs.db), a mixed folder, a disk."""
    media = MediaFactory(data)
    first = media.image(f"{_PHOTOS}/Keep/a.jpg", seed=1)
    second = media.image(f"{_PHOTOS}/Keep/b.jpg", seed=2)
    media.copy(first, f"{_PHOTOS}/Old/Trip/a.jpg")
    media.copy(second, f"{_PHOTOS}/Old/Trip/b.jpg")
    (data / _PHOTOS / "Old" / "Trip" / "Thumbs.db").write_bytes(_THUMBS)
    media.copy(first, f"{_PHOTOS}/Mixed/a.jpg")
    media.image(f"{_PHOTOS}/Mixed/other.jpg", seed=3)
    (data / _PHOTOS / "Before").mkdir()  # empty before the run: stays
    media.copy(second, f"{_BACKUP}/b.jpg")  # a mount root holding only a copy


def _runtime(locations: Locations, cli: Layer | None = None) -> Runtime:
    """A runtime where `c/Photos` and `d/Old disk` are the mounted folders."""
    data = locations.data_dir
    mounts = MountTable(frozenset({data / _PHOTOS, data / _BACKUP}))
    return replace(make_runtime(locations, cli or _KEEP), mounts=mounts)


def _clean(runtime: Runtime, *, delete: bool = False) -> tuple[str, Outcome]:
    """Audit then clean, as `clean --yes` does."""
    findings = AuditService(runtime, NullProgress()).run()
    service = CleanService(runtime, NullProgress())
    service.ensure_ready(CleanMode(delete=delete))
    return service.execute(
        service.feasible(replace(findings.plan, delete_copies=delete))
    )


def test_a_folder_of_copies_goes_and_undo_brings_it_back(locations: Locations) -> None:
    """Trip and then Old are removed, Thumbs.db set aside; undo puts all back."""
    data = locations.data_dir
    _tree(data)
    runtime = _runtime(locations)
    trip = data / _PHOTOS / "Old" / "Trip"
    findings = AuditService(runtime, NullProgress()).run()
    predicted = emptied_by(runtime, findings.plan).predicted()
    run_id, outcome = _clean(runtime)
    assert not trip.parent.exists()
    assert (data / _PHOTOS / "Mixed" / "other.jpg").is_file()
    assert (data / _PHOTOS / "Before").is_dir()
    assert (data / _BACKUP).is_dir()  # a mount root, even empty
    assert outcome.folders_removed == predicted.removed == 2
    assert summarize(locations.journal_dir, run_id).folders_removed == 2
    quarantined = list((locations.quarantine_dir / run_id).rglob("Thumbs.db"))
    assert [path.read_bytes() for path in quarantined] == [_THUMBS]
    undo = undo_run(runtime, run_id, NullProgress())
    assert not undo.failed
    assert sorted(path.name for path in trip.iterdir()) == [
        "Thumbs.db",
        "a.jpg",
        "b.jpg",
    ]
    assert (data / _BACKUP / "b.jpg").is_file()


def test_folders_are_removed_last_in_the_journal(locations: Locations) -> None:
    """The folder removals close the run: undo recreates them first."""
    _tree(locations.data_dir)
    run_id, _outcome = _clean(_runtime(locations))
    actions = [
        e.action for e in read_journal(journal_file(locations.journal_dir, run_id))
    ]
    first = actions.index(ActionKind.QUARANTINE_JUNK)
    assert set(actions[first:]) == {
        ActionKind.QUARANTINE_JUNK,
        ActionKind.REMOVE_FOLDER,
    }


def test_a_stopped_clean_removes_no_folder(locations: Locations) -> None:
    """Ctrl+C: the files under way end, no folder is removed."""
    _tree(locations.data_dir)
    runtime = _runtime(locations)
    findings = AuditService(runtime, NullProgress()).run()
    service = CleanService(runtime, _StopAtFirstFile())
    with pytest.raises(KeyboardInterrupt):
        service.execute(findings.plan)
    assert (locations.data_dir / _PHOTOS / "Old" / "Trip").is_dir()


def test_delete_without_a_quarantine_keeps_a_folder_with_junk(tmp_path: Path) -> None:
    """`--delete`, no quarantine: Thumbs.db has nowhere to go, Trip stays."""
    locations = make_locations(tmp_path, MountKind.QUARANTINE)
    _tree(locations.data_dir)
    runtime = _runtime(locations)
    findings = AuditService(runtime, NullProgress()).run()
    plan = replace(findings.plan, delete_copies=True)
    predicted = emptied_by(runtime, plan).predicted()
    _run_id, outcome = _clean(runtime, delete=True)
    trip = locations.data_dir / _PHOTOS / "Old" / "Trip"
    assert [path.name for path in trip.iterdir()] == ["Thumbs.db"]
    assert outcome.folders_removed == predicted.removed == 0
    assert [verdict.folder for verdict in predicted.kept][:1] == [trip]


def test_protected_folders_and_roots_are_never_candidates(locations: Locations) -> None:
    """Nothing in or below a protected folder, nor a mount root, is ever removed."""
    data = locations.data_dir
    protect: Layer = {"folders": {"protected": ["C:\\Photos\\Safe"]}}
    rules = base_rules(_runtime(locations, protect))
    files = [data / _PHOTOS / "Safe" / "Deep" / "x.jpg", data / _BACKUP / "y.jpg"]
    assert candidates(files, rules) == []
