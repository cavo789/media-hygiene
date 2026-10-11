"""Sidecar writes and their undo, on the edges: something changed in between."""

from __future__ import annotations

from pathlib import Path

from media_hygiene.actions.journal import JournalWriter, read_journal
from media_hygiene.actions.journaled import CleanContext
from media_hygiene.actions.kinds import Phase, Status
from media_hygiene.actions.outcome import Tally
from media_hygiene.actions.xmp_undo import never_written, undo_xmp, xmp_blocker
from media_hygiene.actions.xmp_write import XmpExecutor, XmpJob
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.scan.progress import NullProgress
from media_hygiene.tags.xmp_merge import XmpValues, new_document

_NEW = new_document(XmpValues(("ours",)), "media-hygiene 9.9").to_bytes()


def _write(tmp_path: Path, jobs: list[XmpJob]) -> tuple[Tally, Path]:
    """Run the writes; the tally and the journal."""
    journal = tmp_path / "run.jsonl"
    tally = Tally()
    with JournalWriter.open(journal) as writer:
        context = CleanContext(
            writer,
            HostPathMapper(tmp_path, ()),
            tmp_path / "quarantine",
            NullProgress(),
            Phase.XMP,
        )
        assert not XmpExecutor(context, tally).run(jobs, lambda: False)
    return tally, journal


def test_never_over_a_file_that_appeared_or_changed(tmp_path: Path) -> None:
    """A new name taken since the plan, a sidecar changed since: both left as is."""
    taken = tmp_path / "IMG_1.jpg.xmp"
    taken.write_bytes(b"theirs")
    changed = tmp_path / "IMG_2.xmp"
    changed.write_bytes(b"edited since")
    jobs = [
        XmpJob(tmp_path / "IMG_1.jpg", taken, _NEW, None),
        XmpJob(tmp_path / "IMG_2.jpg", changed, _NEW, b"as read"),
    ]
    tally, journal = _write(tmp_path, jobs)
    assert len(tally.failed) == len(jobs)
    assert taken.read_bytes() == b"theirs"
    assert changed.read_bytes() == b"edited since"
    assert not list(tmp_path.glob("*.tmp"))
    entries = read_journal(journal)
    assert [entry.status for entry in entries] == [Status.PENDING] * len(jobs)
    assert all(never_written(entry) for entry in entries)  # undo leaves them


def test_undo_restores_the_previous_sidecar_and_says_why_not(tmp_path: Path) -> None:
    """The previous bytes come back; without them, or once removed, a reason."""
    sidecar = tmp_path / "IMG_3.xmp"
    sidecar.write_bytes(b"previous")
    tally, journal = _write(
        tmp_path, [XmpJob(tmp_path / "IMG_3.jpg", sidecar, _NEW, b"previous")]
    )
    assert tally.done == 1
    entry = read_journal(journal)[-1]
    assert entry.status is Status.DONE
    assert entry.quarantine is not None
    assert xmp_blocker(entry) is None
    undo_xmp(entry)
    assert sidecar.read_bytes() == b"previous"
    assert xmp_blocker(entry) is not None  # no longer ours
    Path(entry.quarantine).unlink()
    sidecar.write_bytes(_NEW)
    assert "quarantine" in str(xmp_blocker(entry))
    sidecar.unlink()
    assert "gone" in str(xmp_blocker(entry))
