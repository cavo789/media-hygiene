"""Who is on each face: confirmed, nearest reference, ruled out, ignored; sections."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.faces.models import EMBEDDING_SIZE, FaceBox, embedding_bytes
from media_hygiene.index.face_rows import StoredFace
from media_hygiene.people.board import PeopleBoard
from media_hygiene.people.guide import left_to_do, people_list
from media_hygiene.people.known import Known
from media_hygiene.people.naming import NOBODY, FaceName, How, face_id, name_all
from media_hygiene.people.sections import sections_of
from media_hygiene.people.suggest import suggestions
from media_hygiene.people.why import CLOSE, why_named
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


def test_sections_verified_then_attributed_then_others() -> None:
    """Each person: verified, then attributed (groups, suggestions); ignored hidden."""
    chloe = FaceName("Chloé", How.CONFIRMED)
    near = FaceName("Chloé", How.ASSIGNED)
    gone = FaceName("", How.IGNORED)
    names = (NOBODY, NOBODY, NOBODY, near, near, chloe, NOBODY, gone, gone, chloe)
    groups = ((0, 1, 2), (3, 4), (5, 6), (7, 8), (9,))
    sections = sections_of(groups, names)
    assert sections.ignored == 1
    assert [(s.name, s.verified, s.faces) for s in sections.shown] == [
        ("Chloé", True, (5, 9)),
        ("Chloé", False, (3, 4, 6)),
        ("", False, (0, 1, 2)),
    ]


def test_a_confirmed_face_counts_for_its_person_wherever_it_is() -> None:
    """Manon confirmed inside Chloé's group: Manon's, not attributed to Chloé."""
    chloe = FaceName("Chloé", How.CONFIRMED)
    manon = FaceName("Manon", How.CONFIRMED)
    gone = FaceName("", How.IGNORED)
    names = (chloe, chloe, manon, gone, NOBODY)
    sections = sections_of(((0, 1, 2, 3, 4),), names)
    assert [(s.name, s.verified, s.faces) for s in sections.shown] == [
        ("Chloé", True, (0, 1)),
        ("Chloé", False, (4,)),
        ("Manon", True, (2,)),
    ]


def test_sections_leave_out_the_faces_taken_out_of_their_person() -> None:
    """A face rejected for Chloé leaves her attributed faces; an empty one is hidden."""
    chloe = FaceName("Chloé", How.CONFIRMED)
    near = FaceName("Chloé", How.ASSIGNED)
    names = (chloe, chloe, NOBODY, near, near, NOBODY, NOBODY)
    groups = ((0, 1, 2), (3, 4), (5, 6))
    ruled_out = {
        2: frozenset({"Chloé"}),
        3: frozenset({"Chloé"}),
        4: frozenset({"Chloé"}),
        6: frozenset({"Ana"}),
    }
    sections = sections_of(groups, names, ruled_out)
    assert [(s.name, s.verified, s.faces) for s in sections.shown] == [
        ("Chloé", True, (0, 1)),
        ("", False, (5, 6)),
    ]


def small(name: str, side: float, sharpness: float = 80.0) -> StoredFace:
    """Chloé's face again, on another photo, at this size and sharpness."""
    vector = np.zeros(EMBEDDING_SIZE, dtype=np.float32)
    vector[:2] = (0.95, 0.2)
    box = FaceBox(0, 0, side, side)
    path = Path(f"/data/{name}.jpg")
    return StoredFace(path, 0, box, 0.9, sharpness, embedding_bytes(vector))


def test_a_face_the_page_never_shows_gets_no_name_unless_confirmed() -> None:
    """30 px or blurry: not named; confirmed: named; sharp 60 px: named (0316)."""
    tiny, blurry, sharp = small("tiny", 30), small("blurry", 60, 5.0), small("ok", 60)
    every = (CHLOE, tiny, blurry, sharp)
    names = name_all(every, Known.of(every, settings()))
    assert names[1:] == (NOBODY, NOBODY, FaceName("Chloé", How.ASSIGNED))
    confirmed = (face_id(CHLOE.path, 0), face_id(tiny.path, 0))
    named = settings().model_copy(
        update={"person": (Person(name="Chloé", faces=confirmed),)}
    )
    assert name_all((tiny,), Known.of(every, named)) == (
        FaceName("Chloé", How.CONFIRMED),
    )
    anything = settings().model_copy(update={"min_face": 0, "min_sharpness": 0})
    assert all(n.named for n in name_all(every, Known.of(every, anything)))
    assert named_photos(every, Known.of(every, settings())) == (("Chloé", 2),)


def test_why_names_the_reference_the_score_and_a_close_runner() -> None:
    """Assigned: the nearest reference and the likeness; confirmed: no score (0318)."""
    manon = face("manon", (0.9, 0.35))
    between = face("between", (0.98, 0.19))
    every = (CHLOE, manon, between, STRANGER)
    both = settings().model_copy(
        update={
            "person": (
                *settings().person,
                Person(name="Manon", faces=(face_id(manon.path, 0),)),
            )
        }
    )
    known = Known.of(every, both)
    assigned = why_named(between, known)
    assert assigned.how is How.ASSIGNED
    assert assigned.threshold == both.similarity
    nearest = name_all((between,), known)[0].name
    reference = CHLOE if nearest == "Chloé" else manon
    assert assigned.reference == face_id(reference.path, 0)
    assert assigned.score > both.similarity
    assert assigned.runner is not None
    assert assigned.score - assigned.runner.score <= CLOSE
    assert assigned.runner.name != nearest
    confirmed = why_named(CHLOE, known)
    assert (confirmed.how, confirmed.score, confirmed.reference) == (
        How.CONFIRMED,
        0,
        "",
    )
    alone = why_named(STRANGER, known)
    assert alone.how is None
    assert alone.runner is None


def test_people_come_in_alphabetical_order_folded() -> None:
    """Zoé after Émile and chloe, whatever their faces (0324)."""
    zoe = FaceName("Zoé", How.CONFIRMED)
    emile = FaceName("Émile", How.CONFIRMED)
    chloe = FaceName("chloe", How.ASSIGNED)
    names = (zoe, zoe, zoe, emile, chloe, chloe, NOBODY, NOBODY)
    groups = ((0, 1, 2), (3,), (4, 5), (6, 7))
    shown = sections_of(groups, names).shown
    assert [s.name for s in shown] == ["chloe", "Émile", "Zoé", ""]


def test_the_people_list_and_what_is_left() -> None:
    """Counts per person; attributed faces, their people, unnamed groups (0325)."""
    chloe = FaceName("Chloé", How.CONFIRMED)
    near = FaceName("Chloé", How.ASSIGNED)
    ana = FaceName("Ana", How.CONFIRMED)
    gone = FaceName("", How.IGNORED)
    names = (chloe, near, near, ana, NOBODY, NOBODY, NOBODY, gone, gone)
    groups = ((0, 1, 2), (3,), (4, 5), (6,), (7, 8))
    sections = sections_of(groups, names)
    assert people_list(sections) == [
        {"name": "Ana", "verified": 1, "attributed": 0},
        {"name": "Chloé", "verified": 1, "attributed": 2},
    ]
    assert left_to_do(sections) == {
        "attributed": 2,
        "people": 1,
        "unnamed": 2,
        "unnamed_faces": 3,
        "ignored": 1,
    }


def test_an_unnamed_group_says_who_it_looks_like() -> None:
    """Close to Chloé's verified faces: suggested; far: nobody; rejected: not used."""
    every = (CHLOE, CHLOE_OLDER, CHLOE_OLDER, STRANGER, STRANGER)
    board = PeopleBoard(every, ((0,), (1, 2), (3, 4)), 0)
    chloe = FaceName("Chloé", How.CONFIRMED)
    sections = sections_of(board.groups, (chloe, NOBODY, NOBODY, NOBODY, NOBODY))
    found = suggestions(board, sections, {})
    assert found == {1: [{"name": "Chloé", "score": 0.95}]}
    out = frozenset({"Chloé"})
    assert not suggestions(board, sections, {1: out, 2: out})
