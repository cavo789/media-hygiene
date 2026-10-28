"""Black photos written to a folder and listed in a fresh index, keys from 1."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING

from PIL import Image

from media_hygiene.index.schema import prepare

if TYPE_CHECKING:
    from pathlib import Path


def indexed_photos(index: Path, folder: Path, count: int) -> None:
    """Write `IMG_<n>.jpg` photos into `folder` and list them in the index.

    Args:
        index: The index file to create.
        folder: Where the photos go (made if missing).
        count: How many.
    """
    folder.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(index)) as connection:
        prepare(connection)
        for number in range(count):
            photo = folder / f"IMG_{number}.jpg"
            Image.new("RGB", (64, 48)).save(photo)
            connection.execute(
                "INSERT INTO files (path, size, mtime_ns) VALUES (?, ?, 1)",
                (str(photo), photo.stat().st_size),
            )
        connection.commit()
