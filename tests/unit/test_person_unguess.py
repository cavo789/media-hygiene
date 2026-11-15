"""The cross of a face named by the tool on `/person`: "? nobody" in one click."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.faces.models import EMBEDDING_SIZE, FaceBox
from media_hygiene.index.face_rows import StoredFace
from media_hygiene.people.known import Known
from media_hygiene.people.naming import NOBODY, id_of, name_all
from media_hygiene.person.unguess import unguessed_line, without_guesses


def _face(name: str, vector: np.ndarray) -> StoredFace:
    """A sharp, large face of the index.

    Args:
        name: Its photo's name.
        vector: Its vector, normalised here.

    Returns:
        The face.
    """
    unit = (vector / np.linalg.norm(vector)).astype(np.float32)
    return StoredFace(
        Path(f"/data/c/p/{name}.jpg"),
        0,
        FaceBox(0, 0, 200, 200),
        0.9,
        100.0,
        unit.tobytes(),
    )


def _scene() -> tuple[StoredFace, tuple[StoredFace, ...], PeopleSettings]:
    """A face close to Marc, then to Valery; a third person far from it.

    Returns:
        The face, every face, the names.
    """
    rng = np.random.default_rng(3)
    base = rng.standard_normal(EMBEDDING_SIZE)
    marc = _face("marc", base + 0.1 * rng.standard_normal(EMBEDDING_SIZE))
    valery = _face("valery", base + 0.2 * rng.standard_normal(EMBEDDING_SIZE))
    other = _face("other", rng.standard_normal(EMBEDDING_SIZE))
    face = _face("seen", base)
    people = (
        Person(name="Marc", faces=(id_of(marc),)),
        Person(name="Valery", faces=(id_of(valery),)),
        Person(name="Other", faces=(id_of(other),)),
    )
    return face, (marc, valery, other, face), PeopleSettings(person=people)


def test_every_guess_is_ruled_out_at_once() -> None:
    """One click: Marc then Valery ruled out, the face is nobody's; Other untouched."""
    face, every, section = _scene()
    assert name_all((face,), Known.of(every, section))[0].name == "Marc"
    after, ruled = without_guesses(face, every, section)
    assert ruled == ("Marc", "Valery")
    assert name_all((face,), Known.of(every, after))[0] == NOBODY
    assert not after.person[2].rejected
    assert "Marc, Valery" in unguessed_line(after, face)


def test_a_face_nobody_is_guessed_for_is_left_alone() -> None:
    """Nothing guessed: nothing written, the line says so."""
    face, every, section = _scene()
    alone = section.model_copy(update={"person": section.person[2:]})
    after, ruled = without_guesses(face, every, alone)
    assert not ruled
    assert after == alone
    assert unguessed_line(after, face).startswith("Not saved")
