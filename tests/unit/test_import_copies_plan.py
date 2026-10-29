"""The plan of an import's copies: only new files ever go (0478)."""

from __future__ import annotations

from pathlib import Path

from media_hygiene.constants import MediaKind
from media_hygiene.plan.keep_decision import KeepDecision
from media_hygiene.plan.models import CleanPlan
from media_hygiene.scan.models import MediaFile
from media_hygiene.services.import_copies import import_copies


def _file(name: str) -> MediaFile:
    return MediaFile(Path("/data/c") / name, 10, 0, MediaKind.IMAGE)


def _plan(keeper: str, *removable: str) -> CleanPlan:
    group = KeepDecision("d", 10, _file(keeper), tuple(_file(n) for n in removable))
    return CleanPlan(decisions=(group,), broken=())


def test_an_old_copy_stays_when_the_policy_kept_the_new_one() -> None:
    """The keep policy chose the new file: the library's copy is kept instead."""
    new = {Path("/data/c/new.jpg")}
    cut = import_copies(_plan("new.jpg", "old.jpg"), new)
    (group,) = cut.decisions
    assert group.keeper.path == Path("/data/c/old.jpg")
    assert [f.path for f in group.removable] == [Path("/data/c/new.jpg")]


def test_old_copies_are_never_set_aside() -> None:
    """Two library copies of each other: not the import's business."""
    assert import_copies(_plan("a.jpg", "b.jpg"), {Path("/data/c/x.jpg")}).is_empty


def test_two_new_twins_keep_one() -> None:
    """Both new: the policy's choice stands."""
    new = {Path("/data/c/a.jpg"), Path("/data/c/b.jpg")}
    (group,) = import_copies(_plan("a.jpg", "b.jpg"), new).decisions
    assert group.keeper.path == Path("/data/c/a.jpg")
    assert [f.path for f in group.removable] == [Path("/data/c/b.jpg")]
