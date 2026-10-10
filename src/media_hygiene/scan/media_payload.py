"""The picture and sound of an MP4 or MOV video, apart from its metadata.

These files are a sequence of boxes: `mdat` holds the encoded picture and sound,
`moov` the index and the metadata. A copy whose `moov` was rewritten (a rating set in
Windows, a tag added) is not identical to its original, yet its `mdat` boxes are: same
picture, same sound. Their size is read from the box headers alone; their content is
hashed only when that size matches another video's.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, BinaryIO, Final

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

_PAYLOAD: Final = b"mdat"
_HEADER: Final = 8
_LARGE_SIZE: Final = 8  # size 1: a 64-bit size follows the header
_TO_END: Final = 0  # size 0: the box runs to the end of the file
_LARGE: Final = 1
_CHUNK: Final = 1024 * 1024
# ISO base media files only (MP4, MOV, 3GP, M4V): the others are not boxes.
_BOX_SUFFIXES: Final = frozenset({".mp4", ".mov", ".m4v", ".3gp"})


def payload_size(path: Path) -> int | None:
    """Total size of the picture and sound boxes, read from the box headers.

    Args:
        path: A video.

    Returns:
        The size in bytes, None for another format or a file that cannot be read.
    """
    if path.suffix.lower() not in _BOX_SUFFIXES:
        return None
    try:
        with path.open("rb") as stream:
            boxes = list(_payload_boxes(stream))
    except OSError:
        return None
    return sum(size for _start, size in boxes) or None


def payload_digest(path: Path) -> str | None:
    """SHA-256 of the picture and sound boxes, in file order.

    Args:
        path: A video.

    Returns:
        The digest, None for another format or a file that cannot be read.
    """
    if path.suffix.lower() not in _BOX_SUFFIXES:
        return None
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            boxes = list(_payload_boxes(stream))
            for start, size in boxes:
                stream.seek(start)
                left = size
                while left > 0 and (chunk := stream.read(min(left, _CHUNK))):
                    digest.update(chunk)
                    left -= len(chunk)
    except OSError:
        return None
    return digest.hexdigest() if boxes else None


def _payload_boxes(stream: BinaryIO) -> Iterator[tuple[int, int]]:
    """Find the picture and sound boxes of a file.

    Args:
        stream: The open file.

    Yields:
        The offset and size of each box content; nothing when the file is not boxes.
    """
    end = stream.seek(0, 2)
    offset = 0
    while offset + _HEADER <= end:
        stream.seek(offset)
        header = stream.read(_HEADER)
        size, kind = int.from_bytes(header[:4], "big"), header[4:]
        start = offset + _HEADER
        if size == _LARGE:
            size = int.from_bytes(stream.read(_LARGE_SIZE), "big")
            start += _LARGE_SIZE
        elif size == _TO_END:
            size = end - offset
        if size < start - offset or offset + size > end:
            return
        if kind == _PAYLOAD:
            yield start, offset + size - start
        offset += size
