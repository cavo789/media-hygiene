"""The picture and sound boxes of an MP4: sized from headers, hashed apart."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.scan.media_payload import payload_digest, payload_size

if TYPE_CHECKING:
    from pathlib import Path

PICTURE = b"picture and sound" * 100


def box(kind: bytes, content: bytes) -> bytes:
    """One ISO box: 32-bit size, kind, content."""
    return (8 + len(content)).to_bytes(4, "big") + kind + content


def write(path: Path, *boxes: bytes) -> Path:
    """Write a file made of `boxes`."""
    path.write_bytes(b"".join(boxes))
    return path


def test_only_the_metadata_differs(tmp_path: Path) -> None:
    """Same picture and sound, another `moov`: same size and digest of the payload."""
    ftyp = box(b"ftyp", b"isom0000")
    original = write(
        tmp_path / "a.mp4", ftyp, box(b"mdat", PICTURE), box(b"moov", b"x")
    )
    edited = write(tmp_path / "b.MP4", ftyp, box(b"mdat", PICTURE), box(b"moov", b"xy"))
    other = write(tmp_path / "c.mp4", ftyp, box(b"mdat", PICTURE[::-1]))
    assert payload_size(original) == payload_size(edited) == len(PICTURE)
    assert payload_digest(original) == payload_digest(edited)
    assert payload_digest(original) != payload_digest(other)


def test_large_and_open_ended_boxes(tmp_path: Path) -> None:
    """A 64-bit size (size 1) and a box running to the end (size 0) are read."""
    large = (1).to_bytes(4, "big") + b"mdat" + (16 + len(PICTURE)).to_bytes(8, "big")
    first = write(tmp_path / "a.mov", large + PICTURE)
    second = write(tmp_path / "b.mov", (0).to_bytes(4, "big") + b"mdat" + PICTURE)
    assert payload_size(first) == payload_size(second) == len(PICTURE)
    assert payload_digest(first) == payload_digest(second)


def test_nothing_for_other_files(tmp_path: Path) -> None:
    """Another format, a corrupt header, no payload or no file: no answer."""
    avi = write(tmp_path / "a.avi", box(b"mdat", PICTURE))
    corrupt = write(tmp_path / "b.mp4", (999_999).to_bytes(4, "big") + b"mdat")
    empty = write(tmp_path / "c.mp4", box(b"moov", b"x"))
    for path in (avi, corrupt, empty, tmp_path / "missing.mp4"):
        assert payload_size(path) is None
        assert payload_digest(path) is None
