"""The cross of a face named by the tool on `/person`: "? nobody" in one click."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.faces.models import EMBEDDING_SIZE, FaceBox
from media_hygiene.index.face_rows import StoredFace
from media_hygiene.people.known import Known
from media_hygiene.people.naming import NOBODY, id_of, name_all
from media_hygiene.person.unguess import unguessed_line, without_guesses

if TYPE_CHECKING:
    import pytest


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
    assert "Marc, Valery" in unguessed_line(after, face, ruled)


def test_a_face_nobody_is_guessed_for_is_left_alone() -> None:
    """Nothing guessed: nothing written, the line says so."""
    face, every, section = _scene()
    alone = section.model_copy(update={"person": section.person[2:]})
    after, ruled = without_guesses(face, every, alone)
    assert not ruled
    assert after == alone
    assert unguessed_line(after, face, ruled).startswith("Not saved")


def test_the_references_are_gathered_once_for_many_wrong_guesses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Four people alike: four names ruled out, the index's faces gathered once."""
    rng = np.random.default_rng(5)
    base = rng.standard_normal(EMBEDDING_SIZE)
    alike = [
        _face(f"p{n}", base + 0.1 * (n + 1) * rng.standard_normal(EMBEDDING_SIZE))
        for n in range(4)
    ]
    face = _face("seen", base)
    people = tuple(
        Person(name=f"P{n}", faces=(id_of(one),)) for n, one in enumerate(alike)
    )
    every, section = (*alike, face), PeopleSettings(person=people)
    calls: list[int] = []
    real = Known.of

    def counted(*args: object) -> Known:
        calls.append(1)
        return real(*args)  # type: ignore[arg-type]

    monkeypatch.setattr(Known, "of", counted)
    after, ruled = without_guesses(face, every, section)
    assert len(ruled) == 4
    assert len(calls) == 1
    assert name_all((face,), real(every, after))[0] == NOBODY


def test_a_confirmed_face_is_ruled_out_then_the_next_guess() -> None:
    """Confirmed as Marc by mistake: Marc taken off, then Valery guessed, ruled out."""
    face, every, section = _scene()
    marc = section.person[0]
    confirmed = marc.model_copy(update={"faces": (*marc.faces, id_of(face))})
    section = section.model_copy(update={"person": (confirmed, *section.person[1:])})
    after, ruled = without_guesses(face, every, section)
    assert ruled == ("Marc", "Valery")
    assert id_of(face) not in after.person[0].faces
    assert name_all((face,), Known.of(every, after))[0] == NOBODY
