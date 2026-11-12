"""Moving faces from one person to another (TODO 0712)."""

from __future__ import annotations

from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.people.changes import Naming
from media_hygiene.people.moving import move_faces


def settings() -> PeopleSettings:
    """Chloé with three faces."""
    return PeopleSettings(person=(Person(name="Chloé", faces=("a#0", "b#0", "c#0")),))


def test_a_face_leaves_chloe_and_is_ruled_out_of_her() -> None:
    """The face is Manon's, not Chloé's, and never given back to her."""
    moved = move_faces(settings(), Naming("Manon", ("b#0",)), "Chloé")
    chloe, manon = moved.person
    assert chloe.faces == ("a#0", "c#0")
    assert chloe.rejected == ("b#0",)
    assert manon.name == "Manon"
    assert manon.faces == ("b#0",)


def test_an_unnamed_group_or_the_same_name_rules_nobody_out() -> None:
    """No source, or the same person: a plain naming."""
    for source in ("", "chloé"):
        moved = move_faces(settings(), Naming("Chloé", ("d#0",)), source)
        assert moved.person[0].rejected == ()
        assert "d#0" in moved.person[0].faces
