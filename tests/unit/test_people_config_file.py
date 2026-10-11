"""`[people]` in config.toml: names written with tomlkit, comments kept, read back."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.people.changes import Naming, give_name, ignore_faces, reject_faces
from media_hygiene.people.config_file import read_people, save_people

if TYPE_CHECKING:
    from pathlib import Path

KEPT = (
    "# my file\n[people]\n# stricter\nsimilarity = 0.4\n\n[tags]\n# words\n"
    "town_km = 5\n"
)


def test_names_are_added_kept_and_removed(tmp_path: Path) -> None:
    """The other settings and comments stay; a person's own comment survives a save."""
    config = tmp_path / "config.toml"
    config.write_text(KEPT)
    chloe = Person(name="Chloé", faces=("/a#0",))
    save_people(config, PeopleSettings(person=(chloe,), ignored=("/s#1",)))
    text = config.read_text().replace('name = "Chloé"', '# her\nname = "Chloé"')
    config.write_text(text)
    written = read_people(config)
    assert written.similarity == pytest.approx(0.4)
    manon = Person(name="Manon", faces=("/b#0",), rejected=("/a#1",))
    save_people(config, written.model_copy(update={"person": (*written.person, manon)}))
    text = config.read_text()
    for kept in ("# my file", "# stricter", "# words", "# her", "town_km = 5"):
        assert kept in text
    assert text.index("[[people.person]]") < text.index("[tags]")
    assert "\n\n\n" not in text
    back = read_people(config)
    assert [person.name for person in back.person] == ["Chloé", "Manon"]
    assert back.person[1].rejected == ("/a#1",)
    save_people(config, back.model_copy(update={"person": (), "ignored": ()}))
    empty = read_people(config)
    assert empty.person == ()
    assert empty.ignored == ()
    assert "[[people.person]]" not in config.read_text()


def test_a_missing_file_is_created(tmp_path: Path) -> None:
    """No file: no name; a save creates it with the section."""
    config = tmp_path / "config.toml"
    assert read_people(config) == PeopleSettings()
    save_people(config, PeopleSettings(person=(Person(name="Léa", faces=("/c#0",)),)))
    assert read_people(config).person[0].name == "Léa"
    assert not (tmp_path / ".config.toml.tmp").exists()


def test_two_people_of_one_name_are_refused(tmp_path: Path) -> None:
    """Names are compared in any case; the file is left untouched."""
    config = tmp_path / "config.toml"
    config.write_text(KEPT)
    twice = (Person(name="Léa", faces=("/a#0",)), Person(name="léa", faces=("/b#0",)))
    with pytest.raises(ValueError, match="two people are named 'léa'"):
        PeopleSettings(person=twice)
    config.write_text("people = 3\n")
    with pytest.raises(TypeError):
        save_people(config, PeopleSettings())


def test_changes_move_faces_between_people() -> None:
    """Naming takes faces from others and from the ignored; empty people go."""
    section = PeopleSettings(
        person=(Person(name="Chloé", faces=("/a#0", "/b#0"), rejected=("/c#0",)),),
        ignored=("/d#0",),
    )
    moved = give_name(section, Naming("Manon", ("/a#0", "/b#0", "/d#0"), ("/e#0",)))
    assert [person.name for person in moved.person] == ["Manon"]
    assert moved.person[0].faces == ("/a#0", "/b#0", "/d#0")
    assert moved.person[0].rejected == ("/e#0",)
    assert moved.ignored == ()
    again = give_name(section, Naming(" chloé ", ("/c#0", "/f#0")))
    assert again.person[0].name == "Chloé"
    assert again.person[0].faces == ("/a#0", "/b#0", "/c#0", "/f#0")
    assert again.person[0].rejected == ()
    ignored = ignore_faces(section, ("/a#0",))
    assert ignored.ignored == ("/d#0", "/a#0")
    assert ignored.person[0].faces == ("/b#0",)
    rejected = reject_faces(section, Naming("CHLOÉ", ("/b#0",)))
    assert rejected.person[0].faces == ("/a#0",)
    assert rejected.person[0].rejected == ("/c#0", "/b#0")
    assert reject_faces(section, Naming("Nobody", ("/a#0",))) is section
