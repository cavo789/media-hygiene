"""`mh backup`'s plan (0264): each case of a file, planned as the TODO says.

Unchanged, new, edited, moved (by `sort`, by hand), moved identical twins, gone by
each reason, a broken PC file, the safety stop; paths compared without case, times
within robocopy's two seconds.
"""

from __future__ import annotations

from typing import Final

import pytest

from media_hygiene.plan.backup_entries import SAME_TIME_NS, Entry, Stat
from media_hygiene.plan.backup_gone import GoneReason
from media_hygiene.plan.backup_target import BackupInputs, plan_backup

_T: Final = 1_700_000_000_000_000_000
A: Final = Stat(100, _T)
B: Final = Stat(200, _T)


def never(_new: str, _old: str) -> bool:
    """No two files hold the same content."""
    return False


def always(_new: str, _old: str) -> bool:
    """Every two files hold the same content."""
    return True


def test_the_same_file_is_left_alone() -> None:
    """Same path, size and time: nothing to do."""
    plan = plan_backup(BackupInputs({"C/P/a.jpg": A}, {"C/P/a.jpg": A}), never)
    assert plan.unchanged == 1
    assert not plan.copies
    assert not plan.gone


def test_robocopy_s_two_seconds_and_case_are_the_same() -> None:
    """A NAS keeping times to the second, a name written otherwise: unchanged."""
    there = Stat(A.size, A.mtime_ns + SAME_TIME_NS)
    plan = plan_backup(BackupInputs({"C/P/a.jpg": A}, {"C/P/A.JPG": there}), never)
    assert plan.unchanged == 1
    assert not plan.gone


def test_a_new_file_is_copied() -> None:
    """On the PC only: copied."""
    plan = plan_backup(BackupInputs({"C/P/a.jpg": A}, {}), never)
    assert plan.new == (Entry("C/P/a.jpg", A),)
    assert plan.copies == plan.new


def test_an_edited_file_is_set_aside_then_copied() -> None:
    """Same path, another size: the backup's copy first set aside."""
    plan = plan_backup(BackupInputs({"C/P/a.jpg": B}, {"C/P/a.jpg": A}), never)
    (edit,) = plan.edited
    assert edit.old == Entry("C/P/a.jpg", A)
    assert edit.new == Entry("C/P/a.jpg", B)
    assert plan.copies == (edit.new,)


def test_a_broken_pc_file_never_replaces_its_copy() -> None:
    """The audit found it broken: the backup's copy kept, listed apart."""
    inputs = BackupInputs(
        {"C/P/a.jpg": B}, {"C/P/a.jpg": A}, broken=frozenset({"C/P/a.jpg"})
    )
    plan = plan_backup(inputs, never)
    assert not plan.edited
    assert plan.broken == (Entry("C/P/a.jpg", B),)
    assert not plan.copies


def test_a_file_moved_by_sort_is_renamed_on_the_backup() -> None:
    """Gone from one path, new at another, same size, time and content: a move."""
    inputs = BackupInputs({"C/P/2024/Noel/a.jpg": A}, {"C/P/Unsorted/a.jpg": A})
    plan = plan_backup(inputs, always)
    (move,) = plan.moves
    assert move.old == Entry("C/P/Unsorted/a.jpg", A)
    assert move.new == "C/P/2024/Noel/a.jpg"
    assert not plan.copies
    assert not plan.gone


def test_a_file_renamed_by_hand_is_renamed_too() -> None:
    """A new name in the Explorer: the same rename on the backup."""
    plan = plan_backup(BackupInputs({"C/P/beach.jpg": A}, {"C/P/a.jpg": A}), always)
    assert [move.new for move in plan.moves] == ["C/P/beach.jpg"]


def test_another_content_is_no_move() -> None:
    """Same size and time, other bytes: a new file, and a gone one."""
    plan = plan_backup(BackupInputs({"C/P/b.jpg": A}, {"C/P/a.jpg": A}), never)
    assert not plan.moves
    assert [entry.path for entry in plan.new] == ["C/P/b.jpg"]
    assert [gone.entry.path for gone in plan.gone] == ["C/P/a.jpg"]


def test_another_time_is_no_move_and_the_content_is_not_read() -> None:
    """A time three seconds away: never compared."""
    asked: list[tuple[str, str]] = []

    def same(new: str, old: str) -> bool:
        asked.append((new, old))
        return True

    there = Stat(A.size, A.mtime_ns + 3 * SAME_TIME_NS)
    plan = plan_backup(BackupInputs({"C/P/b.jpg": A}, {"C/P/a.jpg": there}), same)
    assert not plan.moves
    assert not asked


def test_identical_twins_are_paired_by_name() -> None:
    """Identical copies are paired by name.

    Two identical PC files, one old copy: the first by name takes it, the other is
    copied; two old copies: each pairs with one, in name order.
    """
    plan = plan_backup(
        BackupInputs({"C/P/x/b.jpg": A, "C/P/x/a.jpg": A}, {"C/P/old.jpg": A}), always
    )
    assert [(m.old.path, m.new) for m in plan.moves] == [("C/P/old.jpg", "C/P/x/a.jpg")]
    assert [entry.path for entry in plan.new] == ["C/P/x/b.jpg"]
    plan = plan_backup(
        BackupInputs(
            {"C/P/x/b.jpg": A, "C/P/x/a.jpg": A}, {"C/P/old2.jpg": A, "C/P/old1.jpg": A}
        ),
        always,
    )
    assert [(m.old.path, m.new) for m in plan.moves] == [
        ("C/P/old1.jpg", "C/P/x/a.jpg"),
        ("C/P/old2.jpg", "C/P/x/b.jpg"),
    ]


@pytest.mark.parametrize(
    ("reason", "removed"),
    [
        (GoneReason.PURGED, True),
        (GoneReason.CONFIRMED, True),
        (GoneReason.QUARANTINE, False),
        (GoneReason.PENDING, False),
        (GoneReason.UNKNOWN, False),
    ],
)
def test_a_file_gone_is_removed_only_when_purged_or_confirmed(
    reason: GoneReason, *, removed: bool
) -> None:
    """A deletion by mistake is never carried over to the backup."""
    inputs = BackupInputs({}, {"C/P/a.jpg": A}, reasons={"C/P/a.jpg": reason})
    plan = plan_backup(inputs, never)
    assert bool(plan.removals) is removed
    assert bool(plan.kept) is not removed
    assert plan.gone[0].reason is reason


def test_a_file_gone_without_reason_is_unknown() -> None:
    """Nothing known: kept."""
    plan = plan_backup(BackupInputs({}, {"C/P/a.jpg": A}), never)
    assert plan.kept[0].reason is GoneReason.UNKNOWN


def test_the_safety_stop() -> None:
    """More set aside and replaced than the share allowed: the plan stops."""
    target = {f"C/P/{n}.jpg": A for n in range(10)}
    source = {f"C/P/{n}.jpg": A for n in range(8)} | {"C/P/8.jpg": B}
    reasons = {"C/P/9.jpg": GoneReason.PURGED}
    plan = plan_backup(BackupInputs(source, target, reasons=reasons), never)
    assert len(plan.edited) + len(plan.removals) == 2  # 20 % of 10
    assert not plan.stops(20)
    assert plan.stops(19)


def test_moves_never_stop_and_an_empty_backup_never_stops() -> None:
    """A whole library moved by sort, or a first backup: not a reason to stop."""
    moved = plan_backup(BackupInputs({"C/P/new/a.jpg": A}, {"C/P/a.jpg": A}), always)
    assert not moved.stops(0)
    assert not plan_backup(BackupInputs({"C/P/a.jpg": A}, {}), never).stops(0)
