"""After an import, the new exact copies set aside, then undone (0478)."""

from __future__ import annotations

import io
import os
from typing import TYPE_CHECKING

from PIL import Image

from media_hygiene.actions.journal import journal_file, read_journal
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.import_copies import set_aside_copies
from media_hygiene.services.undo import resolve_run_id, undo_run
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations

_OLD = 1_500_000_000


def _jpeg(color: str) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), color).save(buffer, "JPEG")
    return buffer.getvalue()


def _write(path: Path, content: bytes, *, old: bool = False) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    if old:
        os.utime(path, (_OLD, _OLD))
    return path


def test_new_copies_go_to_the_quarantine_and_come_back(locations: Locations) -> None:
    """Twice the same photo, one already in the library: the 2 new copies set aside."""
    root = locations.data_dir / "c" / "Photos"
    library = _write(root / "2020" / "trip.jpg", _jpeg("red"), old=True)
    phone = root / "Phone"
    first = _write(phone / "IMG_1.jpg", _jpeg("red"))
    twin = _write(phone / "IMG_2.jpg", _jpeg("blue"))
    whatsapp = _write(phone / "IMG-WA0001.jpg", _jpeg("blue"))
    unique = _write(phone / "IMG_3.jpg", _jpeg("green"))
    runtime = make_runtime(locations)
    new = (first, twin, whatsapp, unique)
    assert set_aside_copies(runtime, new) == 2
    assert library.exists()
    assert not first.exists()
    assert unique.exists()
    assert twin.exists() != whatsapp.exists()
    run_id = resolve_run_id(runtime, None)
    assert read_journal(journal_file(locations.journal_dir, run_id))
    undo_run(runtime, run_id, NullProgress())
    assert all(path.exists() for path in new)


def test_nothing_new_nothing_done(locations: Locations) -> None:
    """No new file: no audit, no run."""
    assert set_aside_copies(make_runtime(locations), ()) == 0
    assert not locations.journal_dir.exists() or not any(
        locations.journal_dir.iterdir()
    )
