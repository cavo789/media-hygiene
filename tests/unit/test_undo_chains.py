"""Which actions of an undo run at once, which wait for others (0161)."""

from __future__ import annotations

from media_hygiene.actions.journal import JournalEntry
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.reversal import reversal_of
from media_hygiene.actions.undo_chains import Undoing, chains, stages


def undoing(seq: int, action: ActionKind, path: str, **paths: str) -> Undoing:
    """One journaled action and its reversal."""
    entry = JournalEntry(
        seq=seq,
        phase=Phase.SORT,
        status=Status.DONE,
        action=action,
        path=path,
        host_path=path,
        size=1,
        mtime_ns=1,
    ).model_copy(update=paths)
    return entry, reversal_of(entry)


def seqs(found: tuple[tuple[Undoing, ...], ...]) -> list[list[int]]:
    """The sequence numbers of each chain."""
    return [[entry.seq for entry, _reversal in chain] for chain in found]


def test_unrelated_files_are_each_a_chain_of_their_own() -> None:
    """Files touching other paths may all come back at once."""
    actions = [
        undoing(
            index,
            ActionKind.QUARANTINE_DUPLICATE,
            f"/d/{index}",
            quarantine=f"/q/{index}",
        )
        for index in (3, 2, 1)
    ]
    assert seqs(chains(actions)) == [[3], [2], [1]]


def test_a_name_taken_after_a_move_is_one_chain_newest_first() -> None:
    """`a` moved to `b`, then `c` moved to `a`: `a` comes back only once `c` left it."""
    first = undoing(1, ActionKind.MOVE, "/d/a", target="/t/b")
    other = undoing(2, ActionKind.QUARANTINE, "/d/x", quarantine="/q/x")
    second = undoing(3, ActionKind.MOVE, "/d/c", target="/d/a")
    assert seqs(chains([second, other, first])) == [[3, 1], [2]]


def test_chains_join_through_any_shared_path() -> None:
    """A path shared with two chains merges them, in their order."""
    one = undoing(1, ActionKind.MOVE, "/d/a", target="/t/a")
    two = undoing(2, ActionKind.MOVE, "/d/b", target="/t/b")
    three = undoing(3, ActionKind.MOVE, "/t/a", target="/d/b")
    assert seqs(chains([three, two, one])) == [[3, 2, 1]]


def test_copies_of_one_kept_file_come_back_at_once() -> None:
    """The kept file is only read: its copies are rebuilt side by side."""
    actions = [
        undoing(index, ActionKind.DELETE_DUPLICATE, f"/d/{index}", keeper="/d/kept")
        for index in (2, 1)
    ]
    assert seqs(chains(actions)) == [[2], [1]]


def test_a_kept_file_changed_by_another_action_waits_for_it() -> None:
    """A path read by one action and changed by another links them."""
    rebuilt = undoing(1, ActionKind.DELETE_DUPLICATE, "/d/copy", keeper="/d/kept")
    moved = undoing(2, ActionKind.MOVE, "/d/kept", target="/t/kept")
    assert seqs(chains([moved, rebuilt])) == [[2, 1]]


def test_folders_and_orphan_sidecars_stay_in_their_order() -> None:
    """A folder action or an orphan sidecar is a stage of its own, between the files."""
    newest_first = [
        undoing(6, ActionKind.REMOVE_FOLDER, "/d/old"),
        undoing(5, ActionKind.MOVE, "/d/old/b", target="/t/new/b"),
        undoing(4, ActionKind.MOVE, "/d/old/a", target="/t/new/a"),
        undoing(3, ActionKind.CREATE_FOLDER, "/t/new"),
        undoing(2, ActionKind.QUARANTINE_SIDECAR, "/d/x.xmp", quarantine="/q/x.xmp"),
        undoing(1, ActionKind.MOVE, "/d/c", target="/t/c"),
    ]
    found = [seqs(stage) for stage in stages(newest_first)]
    assert found == [[[6]], [[5], [4]], [[3]], [[2]], [[1]]]


def test_nothing_to_undo_is_no_stage() -> None:
    """An empty run has no stage."""
    assert not stages([])
