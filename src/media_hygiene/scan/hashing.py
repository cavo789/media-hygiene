"""SHA-256 digests: a cheap partial one to split candidates, a full one to prove it."""

from __future__ import annotations

import hashlib
import os
from typing import TYPE_CHECKING

from media_hygiene.constants import Sizes

if TYPE_CHECKING:
    from pathlib import Path

_ALGORITHM = "sha256"


def partial_digest(path: Path) -> str:
    """Hash the first and last 64 KiB of a file (the whole file when smaller).

    Args:
        path: File to hash.

    Returns:
        Hex digest of the sampled bytes.
    """
    digest = hashlib.new(_ALGORITHM)
    with path.open("rb") as stream:
        digest.update(stream.read(Sizes.PARTIAL_HASH))
        size = stream.seek(0, os.SEEK_END)
        if size > 2 * Sizes.PARTIAL_HASH:
            stream.seek(-Sizes.PARTIAL_HASH, os.SEEK_END)
            digest.update(stream.read(Sizes.PARTIAL_HASH))
        elif size > Sizes.PARTIAL_HASH:
            stream.seek(Sizes.PARTIAL_HASH)
            digest.update(stream.read())
    return digest.hexdigest()


def full_digest(path: Path) -> str:
    """Hash a whole file.

    Args:
        path: File to hash.

    Returns:
        Hex SHA-256 digest.
    """
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, _ALGORITHM).hexdigest()


def identical_digest(kept: Path, copy: Path) -> str | None:
    """Compare two files byte for byte, hashing the copy in the same reading.

    Args:
        kept: The file that stays.
        copy: The file compared with it.

    Returns:
        The SHA-256 of the copy when both are identical, else None.
    """
    digest = hashlib.new(_ALGORITHM)
    with kept.open("rb") as first, copy.open("rb") as second:
        while chunk := second.read(Sizes.HASH_CHUNK):
            if first.read(len(chunk)) != chunk:
                return None
            digest.update(chunk)
        if first.read(1):  # the kept file is longer
            return None
    return digest.hexdigest()
