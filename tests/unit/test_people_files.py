"""The faces of each person in `/config/people/<name>.toml`, linked from config.toml."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.config.loader import load_settings
from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.errors import ConfigError
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.followed import follow_ids
from media_hygiene.people.person_files import file_names, safe_name

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations

CHLOE = Person(name="Chloé", faces=("/a.jpg#0", "/b.jpg#1"), rejected=("/c.jpg#0",))
MANON = Person(name="Manon", faces=("/d.jpg#0",))


def saved(config: Path, *people: Person, ignored: tuple[str, ...] = ()) -> None:
    """Save these people (and ignored faces) into config.toml."""
    save_people(config, PeopleSettings(person=people, ignored=ignored))


def test_the_lists_go_to_a_file_per_person(tmp_path: Path) -> None:
    """config.toml keeps the name and the file; the file the faces; read back whole."""
    config = tmp_path / "config.toml"
    saved(config, CHLOE, MANON, ignored=("/s.jpg#0",))
    text = config.read_text()
    assert 'file = "people/Chloé.toml"' in text
    assert 'ignored_file = "people/ignored.toml"' in text
    assert "#0" not in text
    assert '"/b.jpg#1"' in (tmp_path / "people" / "Chloé.toml").read_text()
    assert '"/s.jpg#0"' in (tmp_path / "people" / "ignored.toml").read_text()
    back = read_people(config)
    assert back.person[0].faces == CHLOE.faces
    assert back.person[0].rejected == CHLOE.rejected
    assert back.person[1].faces == MANON.faces
    assert back.ignored == ("/s.jpg#0",)


def test_inline_lists_are_read_then_moved_on_the_first_save(tmp_path: Path) -> None:
    """A config.toml written before 0300 still loads; the next save moves its lists."""
    config = tmp_path / "config.toml"
    config.write_text(
        '[people]\nignored = ["/s.jpg#0"]\n\n[[people.person]]\n# her\n'
        'name = "Chloé"\nfaces = ["/a.jpg#0"]\n'
    )
    before = read_people(config)
    assert before.person[0].faces == ("/a.jpg#0",)
    save_people(config, before)
    text = config.read_text()
    assert "# her" in text
    assert "/a.jpg#0" not in text
    assert "/s.jpg#0" not in text
    assert read_people(config) == before.model_copy(
        update={
            "person": (
                before.person[0].model_copy(update={"file": "people/Chloé.toml"}),
            ),
            "ignored_file": "people/ignored.toml",
        }
    )


def test_only_the_person_changed_is_written_again(tmp_path: Path) -> None:
    """Manon's file is left alone when only Chloé changes: a click rewrites one."""
    config = tmp_path / "config.toml"
    saved(config, CHLOE, MANON)
    manon = tmp_path / "people" / "Manon.toml"
    chloe = tmp_path / "people" / "Chloé.toml"
    inodes = manon.stat().st_ino, chloe.stat().st_ino
    back = read_people(config)
    more = back.person[0].model_copy(update={"faces": (*CHLOE.faces, "/e.jpg#0")})
    save_people(config, back.model_copy(update={"person": (more, back.person[1])}))
    assert manon.stat().st_ino == inodes[0]
    assert chloe.stat().st_ino != inodes[1]
    assert not list((tmp_path / "people").glob(".*.tmp"))


def test_the_file_of_a_person_gone_is_removed(tmp_path: Path) -> None:
    """A person dropped, or every name forgotten: their files go; a hand link stays."""
    config = tmp_path / "config.toml"
    saved(config, CHLOE, MANON, ignored=("/s.jpg#0",))
    saved(config, CHLOE)
    assert sorted(path.name for path in (tmp_path / "people").iterdir()) == [
        "Chloé.toml"
    ]
    mine = tmp_path / "mine.toml"
    mine.write_text('faces = ["/m.jpg#0"]\n')
    saved(config, Person(name="Léa", faces=("/m.jpg#0",), file="mine.toml"))
    saved(config)
    assert mine.is_file()
    assert not list((tmp_path / "people").iterdir())
    assert read_people(config) == PeopleSettings()


def test_file_names_are_safe_for_windows_and_never_shared() -> None:
    """Forbidden characters, device names, `ignored`, names equal but for case."""
    assert safe_name('Mamie "Jo" 1/2?') == "Mamie _Jo_ 1_2_"
    assert safe_name("Papy.") == "Papy"
    assert safe_name("con") == "_con"
    assert safe_name("Ignored") == "_Ignored"
    twins = (
        Person(name="Ma:non", faces=("/a#0",)),
        Person(name="ma?non", faces=("/b#0",)),
    )
    assert file_names(twins) == ("people/Ma_non.toml", "people/ma_non (2).toml")
    kept = Person(name="Léa", faces=("/c#0",), file="people/lea.toml")
    assert file_names((kept,)) == ("people/lea.toml",)


def test_a_missing_or_foreign_file_is_said_in_one_line(
    tmp_path: Path, locations: Locations
) -> None:
    """Never a traceback, never a person silently emptied."""
    config = locations.config_file
    saved(config, CHLOE)
    (locations.config_dir / "people" / "Chloé.toml").unlink()
    with pytest.raises(ValueError, match=r"people/Chloé\.toml is missing"):
        read_people(config)
    with pytest.raises(ConfigError, match="cannot be read"):
        load_settings(locations)
    outside = tmp_path / "outside.toml"
    outside.write_text("faces = []\n")
    config.write_text(f'[[people.person]]\nname = "X"\nfile = "{outside}"\n')
    with pytest.raises(ValueError, match="not inside the folder"):
        read_people(config)


def test_the_settings_of_a_run_see_the_faces_of_the_files(locations: Locations) -> None:
    """Every reader (search, classify, tags) gets the lists from load_settings."""
    saved(locations.config_file, CHLOE)
    people = load_settings(locations).settings.people
    assert people.person[0].faces == CHLOE.faces


def test_a_photo_moved_by_sort_is_followed_into_the_persons_file(
    tmp_path: Path,
) -> None:
    """The ids follow the moves of the index; the save rewrites the person's file."""
    config = tmp_path / "config.toml"
    saved(config, CHLOE)
    moves = {"/a.jpg": "/2024/a.jpg"}
    present = {"/2024/a.jpg", "/b.jpg", "/c.jpg"}
    save_people(config, follow_ids(read_people(config), moves, present))
    text = (tmp_path / "people" / "Chloé.toml").read_text()
    assert '"/2024/a.jpg#0"' in text
    assert '"/a.jpg#0"' not in text


def test_any_name_or_path_is_written_as_valid_toml(tmp_path: Path) -> None:
    """Quotes, backslashes, accents, tabs, DEL: read back as they were."""
    config = tmp_path / "config.toml"
    odd = ('C:\\Mes "photos"\\été\t1.jpg#0', "/del\x7f.jpg#1", "/ü/日本.jpg#2")
    saved(config, Person(name='Jo "le"\nPapy', faces=odd))
    assert read_people(config).person[0].faces == odd
