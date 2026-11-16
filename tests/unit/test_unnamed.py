"""Every cross on a name: ruled out, left unnamed; put back, both undone."""

from __future__ import annotations

from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.people.changes import Naming
from media_hygiene.people.unnamed import left_unnamed, named_again

_FACE = "/data/c/a.jpg#0"


def test_a_cross_rules_out_and_marks_then_put_back_undoes_both() -> None:
    """Fleur's confirmed face crossed: out of Fleur, unguessed; put back: as before."""
    section = PeopleSettings(person=(Person(name="Fleur", faces=(_FACE, "/b.jpg#0")),))
    crossed = left_unnamed(section, Naming("Fleur", (_FACE,)))
    assert crossed.unguessed == (_FACE,)
    assert _FACE in crossed.person[0].rejected
    assert _FACE not in crossed.person[0].faces
    back = named_again(crossed, Naming("Fleur", (_FACE,)), (_FACE,))
    assert not back.unguessed
    assert _FACE in back.person[0].faces
    assert _FACE not in back.person[0].rejected


def test_a_face_crossed_twice_is_marked_once() -> None:
    """The same face, two crosses: one mark."""
    section = PeopleSettings(
        person=(Person(name="Fleur", faces=("/b.jpg#0",)),), unguessed=(_FACE,)
    )
    assert left_unnamed(section, Naming("Fleur", (_FACE,))).unguessed == (_FACE,)
