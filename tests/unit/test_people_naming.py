"""Who is on each face: confirmed, nearest reference, ruled out, ignored; sections."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.faces.models import EMBEDDING_SIZE, FaceBox, embedding_bytes
from media_hygiene.index.face_rows import StoredFace
from media_hygiene.people.naming import NOBODY, FaceName, How, Known, face_id, name_all
from media_hygiene.people.sections import sections_of
from media_hygiene.services.people_names import named_photos


def face(name: str, axes: tuple[float, ...], number: int = 0) -> StoredFace:
    """A face whose vector points along the first axes given."""
    vector = np.zeros(EMBEDDING_SIZE, dtype=np.float32)
    vector[: len(axes)] = axes
    box = FaceBox(0, 0, 50, 50)
    return StoredFace(
        Path(f"/data/{name}.jpg"), number, box, 0.9, 80.0, embedding_bytes(vector)
    )


CHLOE = face("chloe", (1.0,))
CHLOE_OLDER = face("older", (0.9, 0.3))
STRANGER = face("stranger", (0.0, 0.0, 1.0))
STATUE = face("statue", (0.0, 0.0, 0.0, 1.0))
STATUE_AGAIN = face("statue2", (0.0, 0.0, 0.0, 0.95, 0.1))


def settings(**more: object) -> PeopleSettings:
    """Chloé confirmed on one face; the statue ignored."""
    confirmed = (face_id(CHLOE.path, 0),)
    chloe = Person(name="Chloé", faces=confirmed, **more)  # type: ignore[arg-type]
    return PeopleSettings(person=(chloe,), ignored=(face_id(STATUE.path, 0),))


def test_confirmed_assigned_ignored_and_nobody() -> None:
    """The nearest confirmed face names; the ignored statue keeps its double away."""
    every = (CHLOE, CHLOE_OLDER, STRANGER, STATUE, STATUE_AGAIN)
    known = Known.of(every, settings())
    assert known.people == ("Chloé",)
    names = name_all(every, known)
    assert names[0] == FaceName("Chloé", How.CONFIRMED)
    assert names[1] == FaceName("Chloé", How.ASSIGNED)
    assert names[2] is NOBODY
    assert names[3].how is How.IGNORED
    assert names[4].how is How.IGNORED
    assert [name.named for name in names] == [True, True, False, False, False]
    assert named_photos(every, known) == (("Chloé", 2),)


def test_a_rejected_face_is_never_given_the_name() -> None:
    """A face taken out of Chloé stays unnamed, however close."""
    rejected = (face_id(CHLOE_OLDER.path, 0),)
    names = name_all((CHLOE_OLDER,), Known.of((CHLOE,), settings(rejected=rejected)))
    assert names == (NOBODY,)


def test_without_references_only_ids_count() -> None:
    """A name whose faces left the index names nobody; no vector is needed."""
    known = Known.of((), settings())
    assert not known.people
    assert name_all((CHLOE, STRANGER), known) == (
        FaceName("Chloé", How.CONFIRMED),
        NOBODY,
    )


def test_sections_named_first_then_suggested_then_others() -> None:
    """One person's groups together; a mostly ignored group is counted, not shown."""
    chloe = FaceName("Chloé", How.CONFIRMED)
    near = FaceName("Chloé", How.ASSIGNED)
    gone = FaceName("", How.IGNORED)
    names = (NOBODY, NOBODY, NOBODY, near, near, chloe, chloe, gone, gone, chloe)
    groups = ((0, 1, 2), (3, 4), (5, 6), (7, 8), (9,))
    sections = sections_of(groups, names)
    assert sections.ignored == 1
    assert [(s.name, s.suggested, s.faces) for s in sections.shown] == [
        ("Chloé", "", (5, 6, 9)),
        ("", "Chloé", (3, 4)),
        ("", "", (0, 1, 2)),
    ]


def test_sections_leave_out_the_faces_taken_out_of_their_person() -> None:
    """A face rejected for Chloé leaves her section and her suggestion, not others."""
    chloe = FaceName("Chloé", How.CONFIRMED)
    near = FaceName("Chloé", How.ASSIGNED)
    names = (chloe, chloe, NOBODY, near, near, NOBODY, NOBODY)
    groups = ((0, 1, 2), (3, 4), (5, 6))
    ruled_out = {
        2: frozenset({"Chloé"}),
        4: frozenset({"Chloé"}),
        6: frozenset({"Ana"}),
    }
    sections = sections_of(groups, names, ruled_out)
    assert [(s.name, s.suggested, s.faces) for s in sections.shown] == [
        ("Chloé", "", (0, 1)),
        ("", "Chloé", (3,)),
        ("", "", (5, 6)),
    ]
