"""Photos turned, journaled, then undone byte for byte; refusals kept by path (0802)."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PIL import Image

from media_hygiene.actions.journal import read_journal
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.outcome import Tally
from media_hygiene.actions.restore import perform
from media_hygiene.actions.reversal import blocker, reversal_of
from media_hygiene.actions.turn_undo import never_turned
from media_hygiene.actions.turn_write import TurnExecutor, TurnJob
from media_hygiene.actions.undo_pending import never_happened
from media_hygiene.constants import MediaKind
from media_hygiene.index.facts import FileFacts
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.turn_refusals import TurnRefusals
from media_hygiene.scan.models import MediaFile
from media_hygiene.services.turn_apply import TurnScope, turn_jobs
from tests.support.journaled import JOURNAL_NAME, journaled

if TYPE_CHECKING:
    from pathlib import Path

_ORIENTATION = 0x0112
_OLD_TIME = 1_600_000_000_000_000_000


def _photo(path: Path) -> Path:
    """A camera JPEG whose orientation tag says nothing, with an old mtime."""
    exif = Image.Exif()
    exif[_ORIENTATION] = 1
    Image.new("RGB", (40, 20), "red").save(path, "JPEG", exif=exif)
    os.utime(path, ns=(_OLD_TIME, _OLD_TIME))
    return path


def _turn(tmp_path: Path, jobs: list[TurnJob]) -> tuple[Tally, Path]:
    """Run the turns; the tally and the journal."""
    tally = Tally()
    with journaled(tmp_path, Phase.TURN) as context:
        assert not TurnExecutor(context, tally).run(jobs, lambda: False)
    return tally, tmp_path / JOURNAL_NAME


def test_apply_then_undo_gives_the_file_byte_for_byte(tmp_path: Path) -> None:
    """Turned: the tag is 6, journaled done; undone: same bytes, same mtime."""
    path = _photo(tmp_path / "a.jpg")
    before = path.read_bytes()
    tally, journal = _turn(tmp_path, [TurnJob(path, 6)])
    assert tally.done == 1
    with Image.open(path) as image:
        assert image.getexif()[_ORIENTATION] == 6
    assert path.stat().st_mtime_ns != _OLD_TIME  # a new version for the index
    entry = read_journal(journal)[-1]
    assert entry.status is Status.DONE
    assert entry.action is ActionKind.TURN
    reversal = reversal_of(entry)
    assert blocker(entry, reversal) is None
    assert not never_happened(entry, reversal)
    perform(entry, reversal)
    assert path.read_bytes() == before
    assert path.stat().st_mtime_ns == _OLD_TIME
    assert blocker(entry, reversal) is not None  # no longer ours: not undone twice
    assert not list(tmp_path.glob("*.turn"))


def test_a_photo_edited_since_is_kept_and_a_stopped_turn_never_happened(
    tmp_path: Path,
) -> None:
    """Edited after the turn: undo refuses; changed before: the turn fails."""
    path = _photo(tmp_path / "a.jpg")
    _tally, journal = _turn(tmp_path, [TurnJob(path, 8)])
    entry = read_journal(journal)[-1]
    path.write_bytes(path.read_bytes() + b"edited")
    assert "changed since" in str(blocker(entry, reversal_of(entry)))
    pending = entry.model_copy(update={"status": Status.PENDING})
    assert never_turned(pending)
    plain = tmp_path / "b.jpg"
    Image.new("RGB", (8, 8)).save(plain, "JPEG")  # no orientation entry
    tally, _journal = _turn(tmp_path, [TurnJob(plain, 6)])
    assert len(tally.failed) == 1
    assert tally.done == 0


def test_jobs_leave_out_refused_protected_and_not_jpeg(tmp_path: Path) -> None:
    """Only a JPEG proposed, not refused, outside the folders never written."""
    kept = tmp_path / "Protected"
    proposed = (
        (tmp_path / "a.jpg", 90),
        (tmp_path / "b.JPEG", 270),
        (tmp_path / "c.jpg", 180),
        (kept / "d.jpg", 90),
        (tmp_path / "e.heic", 90),
    )
    jobs = turn_jobs(proposed, TurnScope({tmp_path / "c.jpg"}, (kept,)))
    assert jobs == (TurnJob(tmp_path / "a.jpg", 6), TurnJob(tmp_path / "b.JPEG", 8))


def test_refusals_follow_sort_undo_and_renames_and_leave_with_the_file(
    tmp_path: Path,
) -> None:
    """A move (sort, undo, a rename the audit recognises) carries the refusal."""
    path = tmp_path / "a.jpg"
    with FactsRepository.open(tmp_path / "index.sqlite") as repository:
        repository.put(MediaFile(path, 10, 1, MediaKind.IMAGE), FileFacts())
        refusals = TurnRefusals(repository.connection)
        refusals.refuse([path])
        assert refusals.refused() == {path}
        sorted_path = tmp_path / "2024" / "a.jpg"
        repository.move([(str(path), str(sorted_path))])  # `sort`
        assert refusals.refused() == {sorted_path}
        repository.move([(str(sorted_path), str(path))])  # `undo`
        renamed = tmp_path / "Renamed" / "a.jpg"
        repository.move([(str(path), str(renamed))])  # Explorer, `index.rematch`
        assert refusals.refused() == {renamed}
        refusals.take_back([renamed])
        assert not refusals.refused()
        refusals.refuse([renamed])
        repository.forget([str(renamed)])  # the audit finds it gone
        assert not refusals.refused()
