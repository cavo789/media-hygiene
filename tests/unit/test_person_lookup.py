"""The faces of one photo, by a lookup of the faces read once, forgotten on refresh."""

from __future__ import annotations

from pathlib import Path

from media_hygiene.faces.models import FaceBox
from media_hygiene.index.face_rows import StoredFace
from media_hygiene.person.lookup import FaceIndex

BOX = FaceBox(0, 0, 60, 60)
A = Path("/data/c/a.jpg")
B = Path("/data/c/b.jpg")


def _face(path: Path, number: int) -> StoredFace:
    return StoredFace(path, number, BOX, 0.9, 1.0, b"\x01" * 8)


def test_each_photo_gets_its_faces_in_their_order_and_a_refresh_reads_again() -> None:
    """Faces of two photos mixed: each photo's, in order; none for a third photo."""
    index = FaceIndex(None)
    index.__dict__["every"] = (_face(A, 0), _face(B, 0), _face(A, 1))  # as read once
    assert [face.number for face in index.of(A)] == [0, 1]
    assert [face.path for face in index.of(B)] == [B]
    assert index.of(Path("/data/c/c.jpg")) == ()
    index.refresh()  # a face drawn by hand (0715): read the faces again
    index.__dict__["every"] = (*index.__dict__.get("every", ()), _face(B, 1))
    assert [face.number for face in index.of(B)] == [1]
    assert index.of(A) == ()
