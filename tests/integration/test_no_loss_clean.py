"""`clean` erases nothing by default; `--delete` never deletes the kept file itself."""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

import pytest

from media_hygiene.actions.clean import CleanExecutor
from media_hygiene.actions.journal import journal_file, read_journal
from media_hygiene.actions.journaled import JournaledChanges
from media_hygiene.actions.kinds import ActionKind, Phase
from media_hygiene.actions.outcome import Tally
from media_hygiene.actions.sort_cleanup import FolderCleaner
from media_hygiene.actions.sort_folders import FolderRules
from media_hygiene.constants import MediaKind
from media_hygiene.errors import MountError
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.plan.models import CleanPlan, KeepDecision
from media_hygiene.scan.models import MediaFile
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.clean import CleanMode, CleanService
from media_hygiene.services.undo import undo_run
from tests.integration.test_clean_undo import clean, manifest
from tests.support.demo import build_demo
from tests.support.journaled import journaled
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations

EMPTY = hashlib.sha256(b"").hexdigest()


def test_clean_moves_every_copy_to_the_quarantine_and_undo_brings_it_back(
    locations: Locations,
) -> None:
    """No `DELETE_DUPLICATE` by default: the copies wait in the quarantine, whole."""
    build_demo(locations.data_dir)
    before = manifest(locations.data_dir)
    runtime = make_runtime(locations)
    run_id = clean(runtime)
    actions = {
        entry.action
        for entry in read_journal(journal_file(locations.journal_dir, run_id))
    }
    assert ActionKind.QUARANTINE_DUPLICATE in actions
    assert ActionKind.DELETE_DUPLICATE not in actions
    after = manifest(locations.data_dir)
    gone = {digest for name, (digest, _) in before.items() if name not in after}
    kept = {
        digest for digest, _ in manifest(locations.quarantine_dir / run_id).values()
    }
    assert gone - {EMPTY} <= kept  # only empty files are deleted: they hold nothing
    assert not undo_run(runtime, run_id, NullProgress()).failed
    assert manifest(locations.data_dir) == before


def test_clean_without_a_quarantine_refuses_unless_delete(tmp_path: Path) -> None:
    """Nowhere to set the copies aside: refused, `--delete` named as the way out."""
    runtime = make_runtime(make_locations(tmp_path, MountKind.QUARANTINE))
    service = CleanService(runtime, NullProgress())
    with pytest.raises(MountError, match="to /quarantine") as refused:
        service.ensure_ready()
    assert "--delete" in (refused.value.tip or "")
    service.ensure_ready(CleanMode(delete=True))


def run_clean(tmp_path: Path, plan: CleanPlan) -> Tally:
    """Execute a plan with `--delete`, journaled under `tmp_path`."""
    with journaled(tmp_path, delete=True) as context:
        outcome = CleanExecutor(context).run(plan)
    return Tally(skipped=list(outcome.skipped), done=outcome.done)


def photo(path: Path) -> MediaFile:
    """Describe a file as the audit saw it."""
    info = path.stat()
    return MediaFile(path, info.st_size, info.st_mtime_ns, MediaKind.IMAGE)


def test_delete_never_removes_the_kept_file_reached_through_a_hard_link(
    tmp_path: Path,
) -> None:
    """Same inode under two names: skipped, both names stay."""
    keeper, alias = tmp_path / "a.jpg", tmp_path / "b.jpg"
    keeper.write_bytes(b"photo")
    alias.hardlink_to(keeper)
    decision = KeepDecision("digest", 5, photo(keeper), (photo(alias),))
    tally = run_clean(tmp_path, CleanPlan((decision,), ()))
    assert tally.done == 0
    assert "the kept copy itself" in tally.skipped[0].reason
    assert keeper.exists()
    assert alias.exists()


def test_delete_compares_the_bytes_again_before_deleting(tmp_path: Path) -> None:
    """Same size, other bytes since the audit: never deleted."""
    keeper, copy = tmp_path / "a.jpg", tmp_path / "b.jpg"
    keeper.write_bytes(b"photo")
    copy.write_bytes(b"photo")
    decision = KeepDecision("digest", 5, photo(keeper), (photo(copy),))
    copy.write_bytes(b"PHOTO")
    tally = run_clean(tmp_path, CleanPlan((decision,), ()))
    assert "no longer identical" in tally.skipped[0].reason
    assert copy.read_bytes() == b"PHOTO"


def test_a_media_file_is_never_junk(tmp_path: Path) -> None:
    """Even if the rules said so, a photo left in an emptied folder keeps the folder."""
    folder = tmp_path / "Party"
    folder.mkdir()
    (folder / "IMG_1.jpg").write_bytes(b"photo")
    tally = Tally()
    with journaled(tmp_path, Phase.SORT) as context:
        rules = FolderRules(frozenset({"img_1.jpg"}), frozenset({tmp_path}))
        report = FolderCleaner(JournaledChanges(context, tally), tally).run(
            [folder], rules
        )
    assert report.removed == 0
    assert "never junk" in tally.failed[0].reason
    assert (folder / "IMG_1.jpg").read_bytes() == b"photo"


def test_a_quarantine_inside_the_photos_stops_the_audit(locations: Locations) -> None:
    """The audit would read the files set aside: refused, before any walk."""
    build_demo(locations.data_dir)
    inside = locations.model_copy(
        update={"quarantine_dir": locations.data_dir / "c" / "quarantine"}
    )
    with pytest.raises(MountError, match="quarantine folder"):
        AuditService(make_runtime(inside), NullProgress()).run()
