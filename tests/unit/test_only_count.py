"""The home page's count of the only copies, from the index (no disk check per file)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.journal import JournalWriter, journal_file
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.services.only_count import only_count
from tests.support.indexed_photos import indexed_photos
from tests.support.journaled import done_line

if TYPE_CHECKING:
    from pathlib import Path

_RUN = "20261110-100000"


def _set_aside(tmp_path: Path, keeper: Path, size: int) -> Path:
    """A journal with one exact copy of `keeper` and one near duplicate set aside."""
    journals = tmp_path / "journal"
    journals.mkdir()
    with JournalWriter.open(journal_file(journals, _RUN)) as journal:
        for seq, action in enumerate(
            (ActionKind.QUARANTINE_DUPLICATE, ActionKind.QUARANTINE), 1
        ):
            journal.record(
                done_line(
                    action,
                    f"/data/c/{seq}.jpg",
                    seq=seq,
                    size=size,
                    keeper=str(keeper),
                    quarantine=f"/quarantine/{_RUN}/{seq}.jpg",
                )
            )
    return journals


def test_twin_in_the_index_covers_its_copy(tmp_path: Path) -> None:
    """The exact copy is covered when the index holds its twin, same size."""
    index = tmp_path / "index.sqlite"
    indexed_photos(index, tmp_path / "photos", 1)
    keeper = tmp_path / "photos" / "IMG_0.jpg"
    journals = _set_aside(tmp_path, keeper, keeper.stat().st_size)
    assert only_count(index, journals, [_RUN]) == 1  # the near duplicate
    assert only_count(index, journals, [_RUN, "20261001-100000"]) == 1  # lost: out


def test_other_size_or_no_index(tmp_path: Path) -> None:
    """Another size uncovers it; without an index, the card cannot tell."""
    index = tmp_path / "index.sqlite"
    indexed_photos(index, tmp_path / "photos", 1)
    journals = _set_aside(tmp_path, tmp_path / "photos" / "IMG_0.jpg", 1)
    assert only_count(index, journals, [_RUN]) == 2
    assert only_count(None, journals, [_RUN]) is None
    assert only_count(tmp_path / "none.sqlite", journals, [_RUN]) is None
