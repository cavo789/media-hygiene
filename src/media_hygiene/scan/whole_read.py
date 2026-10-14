"""Read a picture once into memory: its decoder and its digests share that reading.

On a Windows folder seen through Docker, reading is what a first audit waits for: a
picture hashed later by the exact-duplicate pass would be read a second time. Memory
stays bounded: one file of at most `[scan] read_whole_mb` per worker; a larger one
is decoded from its path and hashed by the exact-duplicate pass, as before.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from pathlib import Path

# Larger pictures (huge scans, panoramas) are decoded from their path, as before.
# 16 workers x 128 MB: 2 GB at worst, only when 16 such huge files are read at once.
WHOLE_READ_MB: Final = 128
MEBIBYTE: Final = 1024 * 1024
WHOLE_READ_LIMIT: Final = WHOLE_READ_MB * MEBIBYTE


def read_whole(path: Path, limit: int = WHOLE_READ_LIMIT) -> bytes | None:
    """Read every byte of a file not larger than the limit.

    Args:
        path: The file.
        limit: The largest size read at once, in bytes.

    Returns:
        Its bytes, or None when it is too large to hold in memory.

    Raises:
        OSError: The file cannot be read.
    """
    if path.stat().st_size > limit:
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
