"""The cross of a face nobody is named for (0843): ignored for good, and back."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from media_hygiene.config.people_settings import PeopleSettings
from media_hygiene.faces.models import EMBEDDING_SIZE, FaceBox
from media_hygiene.index.face_rows import StoredFace
from media_hygiene.people.changes import ignore_faces
from media_hygiene.people.known import Known
from media_hygiene.people.naming import NOBODY, How, id_of, name_all
from media_hygiene.person.ignore_face import ignored_line, ignored_tag, unignore_faces


def _face(where: str, number: int, vector: np.ndarray) -> StoredFace:
    """A sharp, large face of the index.

    Args:
        where: Its photo's path.
        number: Its number on the photo.
        vector: Its vector, normalised here.

    Returns:
        The face.
    """
    unit = (vector / np.linalg.norm(vector)).astype(np.float32)
    box = FaceBox(0, 0, 200, 200)
    return StoredFace(Path(where), number, box, 0.9, 100.0, unit.tobytes())


def _scene() -> tuple[StoredFace, StoredFace, PeopleSettings]:
    """A reflection ignored, and the same face found again elsewhere.

    Returns:
        The face ignored, the face found again, the names.
    """
    rng = np.random.default_rng(5)
    base = rng.standard_normal(EMBEDDING_SIZE)
    seen = _face("/data/c/p/window.jpg", 0, base)
    # A new scan numbered it 2, and the photo was renamed (sort, Explorer).
    again = _face(
        "/data/c/q/renamed.jpg", 2, base + 0.02 * rng.standard_normal(EMBEDDING_SIZE)
    )
    return seen, again, ignore_faces(PeopleSettings(), (id_of(seen),))


def test_an_ignored_face_found_again_or_moved_is_still_ignored() -> None:
    """Other number, other path: near the ignored one, ignored too, never offered."""
    seen, again, section = _scene()
    known = Known.of((seen, again), section)
    names = name_all((seen, again), known)
    assert [name.how for name in names] == [How.IGNORED, How.IGNORED]
    own = frozenset(section.ignored)
    assert ignored_tag(seen, names[0], own) == {
        "name": "",
        "how": "ignored",
        "not": [],
        "own": True,
    }
    assert ignored_tag(again, names[1], own)["own"] is False  # type: ignore[index]
    assert ignored_tag(seen, NOBODY, own) is None


def test_taken_back_the_face_is_to_name_again() -> None:
    """↩: off the ignored faces, nobody's, the line read back says so."""
    seen, again, section = _scene()
    assert "never offered again" in ignored_line(section, (id_of(seen),), "ignore")
    back = unignore_faces(section, (id_of(seen),))
    assert not back.ignored
    assert name_all((seen,), Known.of((seen, again), back))[0] == NOBODY
    assert "no longer ignored" in ignored_line(back, (id_of(seen),), "unignore")
    assert ignored_line(section, (id_of(seen),), "unignore").startswith("Not saved")
    assert ignored_line(back, (id_of(seen),), "ignore").startswith("Not saved")
