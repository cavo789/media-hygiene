"""A file appearing between a check and an act is never replaced: sort, undo, album."""

from __future__ import annotations

import errno
import hashlib
import os
from pathlib import Path

import pytest

from media_hygiene.actions.album_links import link_blocker
from media_hygiene.actions.journal import JournalEntry, read_journal
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.no_overwrite import rename_no_replace
from media_hygiene.actions.outcome import Tally
from media_hygiene.actions.restore import perform
from media_hygiene.actions.reversal import blocker, reversal_of
from media_hygiene.actions.sort_moves import Relocator, SortContext, file_of
from tests.support.journaled import JOURNAL_NAME, journaled

PHOTO = b"the only copy of a photo"
NEWCOMER = b"a file that arrived meanwhile"


def entry_of(action: ActionKind, path: Path, **fields: str) -> JournalEntry:
    """A done action of a run on `path`, as the journal holds it."""
    return JournalEntry(
        seq=1,
        phase=Phase.CLEAN,
        status=Status.DONE,
        action=action,
        path=str(path),
        host_path=str(path),
        size=len(PHOTO),
        mtime_ns=0,
        sha256=hashlib.sha256(PHOTO).hexdigest(),
    ).model_copy(update=fields)


@pytest.mark.parametrize(
    ("action", "field"),
    [
        (ActionKind.MOVE, "target"),
        (ActionKind.QUARANTINE_DUPLICATE, "quarantine"),
        (ActionKind.DELETE_DUPLICATE, "keeper"),
        (ActionKind.DELETE_EMPTY, ""),
    ],
)
def test_undo_never_replaces_a_file_that_appeared_after_its_check(
    tmp_path: Path, action: ActionKind, field: str
) -> None:
    """Checked free, then taken: refused, the newcomer and the source both whole."""
    path, source = tmp_path / "IMG_1.jpg", tmp_path / "elsewhere" / "IMG_1.jpg"
    source.parent.mkdir()
    source.write_bytes(PHOTO)
    entry = entry_of(action, path, **({field: str(source)} if field else {}))
    reversal = reversal_of(entry)
    assert blocker(entry, reversal) is None
    path.write_bytes(NEWCOMER)  # the race: after the check, before the act
    with pytest.raises(FileExistsError, match="it already exists"):
        perform(entry, reversal)
    assert path.read_bytes() == NEWCOMER
    assert source.read_bytes() == PHOTO


def test_a_quarantined_file_that_changed_stays_in_the_quarantine(
    tmp_path: Path,
) -> None:
    """Not the file set aside (other digest): nothing moves."""
    path, source = tmp_path / "IMG_1.jpg", tmp_path / "q" / "IMG_1.jpg"
    source.parent.mkdir()
    source.write_bytes(b"something else")
    entry = entry_of(ActionKind.QUARANTINE, path, quarantine=str(source))
    with pytest.raises(OSError, match="does not match"):
        perform(entry, reversal_of(entry))
    assert source.exists()
    assert not path.exists()


@pytest.mark.parametrize("disks", [1, 2])
def test_a_sort_never_moves_onto_a_file_that_appeared_after_its_check(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, disks: int
) -> None:
    """Checked free, then taken: refused, pending in the journal, both files whole.

    On one disk the atomic rename refuses; across two, the exclusive copy does.
    """
    source, target = tmp_path / "a" / "IMG_1.jpg", tmp_path / "t" / "IMG_1.jpg"
    source.parent.mkdir()
    source.write_bytes(PHOTO)

    def racing(first: Path, second: Path) -> None:
        second.write_bytes(NEWCOMER)
        if disks == 1:
            rename_no_replace(first, second)
        raise OSError(errno.EXDEV, os.strerror(errno.EXDEV), str(second))

    monkeypatch.setattr("media_hygiene.actions.sort_moves.rename_no_replace", racing)
    with journaled(tmp_path, Phase.SORT) as changes:
        relocator = Relocator(SortContext(changes, "plan", lambda: False), Tally())
        with pytest.raises(FileExistsError, match="the target exists"):
            relocator.move(file_of(source), target, "row")
    assert (source.read_bytes(), target.read_bytes()) == (PHOTO, NEWCOMER)
    entries = read_journal(tmp_path / JOURNAL_NAME)
    moves = [entry for entry in entries if entry.action is ActionKind.MOVE]
    assert {entry.status for entry in moves} == {Status.PENDING}  # never done


def link_entry(link: Path, original: Path) -> JournalEntry:
    """The `link` action of an album run."""
    return entry_of(ActionKind.LINK, link, keeper=str(original)).model_copy(
        update={"phase": Phase.ALBUM}
    )


def test_an_album_name_goes_only_while_its_original_is_the_same_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A link count that lies, an original gone or replaced: the album name stays."""
    original, link = tmp_path / "IMG_1.jpg", tmp_path / "album" / "IMG_1.jpg"
    original.write_bytes(PHOTO)
    link.parent.mkdir()
    os.link(original, link)
    assert link_blocker(link_entry(link, original)) is None
    with pytest.raises(FileExistsError):  # an album never replaces a file
        os.link(original, link)
    assert "journal does not say" in (link_blocker(link_entry(link, link)) or "")
    original.unlink()
    real_stat = Path.stat

    def lying(path: Path, *, follow_symlinks: bool = True) -> os.stat_result:
        found = real_stat(path, follow_symlinks=follow_symlinks)
        return os.stat_result((*found[:3], 2, *found[4:10]))  # "two names left"

    monkeypatch.setattr(Path, "stat", lying)
    assert "last name" in (link_blocker(link_entry(link, original)) or "")
    monkeypatch.undo()
    original.write_bytes(PHOTO)  # a copy, not the same file
    assert "no longer a name" in (link_blocker(link_entry(link, original)) or "")
    assert link.read_bytes() == PHOTO


def test_undo_removes_only_the_album_marker_itself(tmp_path: Path) -> None:
    """A marker entry naming another file (a damaged journal): that file stays."""
    photo = tmp_path / "IMG_1.jpg"
    photo.write_bytes(PHOTO)
    entry = entry_of(ActionKind.MARK_ALBUM, photo)
    assert "not the marker file" in (blocker(entry, reversal_of(entry)) or "")
    assert photo.read_bytes() == PHOTO
