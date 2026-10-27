"""`mh pull`'s plan: what comes back from the push target, what never does (0376)."""

from __future__ import annotations

from media_hygiene.plan.push_entries import Stat
from media_hygiene.services.pull_plan import PullSides, copied_size, plan_pull

_A = Stat(10, 1_000_000_000_000)
_B = Stat(20, 2_000_000_000_000)


def test_missing_files_come_back_present_ones_stay() -> None:
    """A file gone from the PC is copied; the same one present is not planned."""
    target = {"C/Photos/a.jpg": _A, "C/Photos/b.jpg": _B}
    plan = plan_pull(PullSides(target, {"C/Photos/b.jpg": _B}))
    assert plan.copies == ("C/Photos/a.jpg",)
    assert not plan.kept
    assert copied_size(plan, target) == _A.size


def test_edited_file_on_pc_is_never_overwritten() -> None:
    """Another size or time on the PC: left alone and listed."""
    target = {"C/Photos/a.jpg": _A}
    plan = plan_pull(PullSides(target, {"C/Photos/a.jpg": _B}))
    assert plan.kept == ("C/Photos/a.jpg",)
    assert not plan.copies


def test_time_within_two_seconds_is_the_same_file() -> None:
    """Robocopy's `/FFT` tolerance: not an edit."""
    target = {"C/a.jpg": _A}
    near = Stat(_A.size, _A.mtime_ns + 1_000_000_000)
    plan = plan_pull(PullSides(target, {"C/a.jpg": near}))
    assert plan == plan_pull(PullSides(target, {"C/a.jpg": _A}))
    assert not plan.kept


def test_removed_files_never_come_back() -> None:
    """`.removed/<run>/…` is counted, never copied."""
    target = {".removed/20261020/C/Photos/x.jpg": _A}
    plan = plan_pull(PullSides(target, {}))
    assert plan.removed == (".removed/20261020/C/Photos/x.jpg",)
    assert not plan.copies


def test_moved_file_is_not_copied_twice() -> None:
    """Its content is elsewhere in the folders (moved by `sort`): left out."""
    target = {"C/Photos/old/a.jpg": _A, "C/Photos/b.jpg": _B}
    sides = PullSides(
        target,
        {"C/Photos/2019/a.jpg": _A},
        digests={"C/Photos/old/a.jpg": "aaa", "C/Photos/b.jpg": "bbb"},
        present=frozenset({"aaa"}),
    )
    plan = plan_pull(sides)
    assert plan.moved == ("C/Photos/old/a.jpg",)
    assert plan.copies == ("C/Photos/b.jpg",)


def test_identical_copies_under_two_names_both_come_back_when_gone() -> None:
    """Two names, same content, both gone from the PC: both back, not one."""
    target = {"C/Photos/a.jpg": _A, "C/Photos/a (1).jpg": _A}
    sides = PullSides(
        target, {}, digests=dict.fromkeys(target, "aaa"), present=frozenset()
    )
    assert plan_pull(sides).copies == ("C/Photos/a (1).jpg", "C/Photos/a.jpg")


def test_folder_choice_limits_and_ignores_case() -> None:
    """`--folder` keeps only the files below it, whatever the case."""
    target = {"C/Photos/a.jpg": _A, "D/Videos/v.mp4": _B, "C/Photos2/c.jpg": _A}
    plan = plan_pull(PullSides(target, {}), frozenset({"c/photos"}))
    assert plan.copies == ("C/Photos/a.jpg",)
