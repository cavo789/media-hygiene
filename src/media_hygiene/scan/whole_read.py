"""Read a picture once into memory: its decoder and its digests share that reading.

On a Windows folder seen through Docker, reading is what a first audit waits for: a
picture hashed later by the exact-duplicate pass would be read a second time. Memory
stays bounded: one file of at most `WHOLE_READ_LIMIT` per worker; a larger one
is decoded from its path and hashed by the exact-duplicate pass, as before.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from pathlib import Path

# Larger pictures (huge scans, panoramas) are decoded from their path, as before.
WHOLE_READ_LIMIT: Final = 128 * 1024 * 1024


def read_whole(path: Path) -> bytes | None:
    """Read every byte of a file not larger than the limit.

    Args:
        path: The file.

    Returns:
        Its bytes, or None when it is too large to hold in memory.

    Raises:
        OSError: The file cannot be read.
    """
    if path.stat().st_size > WHOLE_READ_LIMIT:
        return None
    with path.open("rb", buffering=0) as stream:
        return stream.read()


def source_of(path: Path, data: bytes | None) -> Path | io.BytesIO:
    """What a decoder should open: the bytes already read, else the file.

    Args:
        path: The file.
        data: Its bytes, None when they were not read.

    Returns:
        A fresh stream over the bytes, or the path.
    """
    return path if data is None else io.BytesIO(data)
