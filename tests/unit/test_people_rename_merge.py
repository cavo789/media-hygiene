"""0827: rename a person, merge two people; every setting naming them follows."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.file_history import versions_of
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.name_follow import follow_name
from media_hygiene.people.rename_desk import FaceShown, RenameAsked, RenameDesk
from media_hygiene.people.renaming import Renaming, rename

if TYPE_CHECKING:
    from pathlib import Path

ANA = Person(name="Maria-Angela", faces=("/a.jpg#0", "/b.jpg#0", "/c.jpg#0"))
TYPO = Person(
    name="Maria-Angelaela",
    faces=("/b.jpg#0", "/c.jpg#0", "/d.jpg#0"),
    rejected=("/x.jpg#0",),
)
LEO = Person(name="Léo", faces=("/l.jpg#0",))


def _desk(config: Path) -> tuple[RenameDesk, list[PeopleSettings]]:
    """A desk on config.toml, and what it handed back to the page."""
    adopted: list[PeopleSettings] = []
    shown = FaceShown(lambda key: 7 if key == "/a.jpg#0" else None, str)
    return RenameDesk(config, shown, adopted.append), adopted


def _saved(tmp_path: Path, *people: Person) -> Path:
    """config.toml naming these people, each in their file."""
    config = tmp_path / "config.toml"
    config.write_text("# mine\n[general]\n")
    save_people(config, PeopleSettings(person=people))
    return config


def test_a_rename_to_a_free_name_renames_the_file(tmp_path: Path) -> None:
    """One file renamed, config.toml updated, the faces intact, the old one kept."""
    config = _saved(tmp_path, TYPO, LEO)
    desk, adopted = _desk(config)
    said = desk.answer(RenameAsked(name="maria-angelaela", to="Marie"))
    back = read_people(config)
    assert [p.name for p in back.person] == ["Marie", "Léo"]
    assert back.person[0].faces == TYPO.faces
    assert back.person[0].rejected == TYPO.rejected
    assert back.person[0].file == "people/Marie.toml"
    old = tmp_path / "people" / "Maria-Angelaela.toml"
    assert not old.exists()
    assert versions_of(old)
    assert "# mine" in config.read_text()
    assert adopted[-1] == back
    assert "Marie, 3 confirmed faces" in str(said["saved"])


def test_a_rename_check_says_it_before_it_runs(tmp_path: Path) -> None:
    """`check` writes nothing and says what will happen."""
    config = _saved(tmp_path, TYPO)
    before = config.read_text()
    desk, _adopted = _desk(config)
    said = desk.answer(RenameAsked(name=TYPO.name, to="Marie", check=True))
    assert "becomes Marie" in str(said["check"])
    assert config.read_text() == before


def test_a_merge_keeps_each_face_once(tmp_path: Path) -> None:
    """Faces of both, once; rejected merged; the other file gone; both in .history."""
    config = _saved(tmp_path, ANA, TYPO, LEO)
    desk, _adopted = _desk(config)
    check = desk.answer(RenameAsked(name=TYPO.name, to=ANA.name, check=True))["check"]
    assert isinstance(check, dict)
    assert check["sentence"] == (
        "Maria-Angelaela (3 faces) joins Maria-Angela (3 faces). "
        "2 faces in both are kept once."
    )
    desk.answer(RenameAsked(name=TYPO.name, to=ANA.name))
    back = read_people(config)
    assert [p.name for p in back.person] == ["Maria-Angela", "Léo"]
    assert back.person[0].faces == ("/a.jpg#0", "/b.jpg#0", "/c.jpg#0", "/d.jpg#0")
    assert back.person[0].rejected == ("/x.jpg#0",)
    folder = tmp_path / "people"
    assert not (folder / "Maria-Angelaela.toml").exists()
    assert versions_of(folder / "Maria-Angelaela.toml")
    assert versions_of(folder / "Maria-Angela.toml")


def test_named_in_one_and_rejected_in_the_other_waits(tmp_path: Path) -> None:
    """A conflict is shown with its photo; nothing is written until answered."""
    ana = ANA.model_copy(update={"rejected": ("/d.jpg#0",)})
    typo = TYPO.model_copy(update={"rejected": ("/a.jpg#0",)})
    config = _saved(tmp_path, ana, typo)
    before = config.read_text()
    desk, _adopted = _desk(config)
    waiting = desk.answer(RenameAsked(name=typo.name, to=ana.name))["check"]
    assert isinstance(waiting, dict)
    conflicts = waiting["conflicts"]
    assert isinstance(conflicts, list)
    assert {c["key"] for c in conflicts} == {"/d.jpg#0", "/a.jpg#0"}
    assert next(c["photo"] for c in conflicts if c["key"] == "/a.jpg#0") == 7
    assert config.read_text() == before
    desk.answer(RenameAsked(name=typo.name, to=ana.name, named=("/a.jpg#0",)))
    back = read_people(config).person[0]
    assert "/a.jpg#0" in back.faces
    assert "/d.jpg#0" not in back.faces
    assert "/d.jpg#0" in back.rejected


@pytest.mark.parametrize("to", ["maria-angela", "MARIA-ANGELA "])
def test_names_differing_by_case_merge(to: str) -> None:
    """A new name of another person in any case is a merge, never a second person."""
    done = rename(PeopleSettings(person=(ANA, TYPO)), Renaming(TYPO.name, to))
    assert done.into == "Maria-Angela"
    assert [p.name for p in done.section.person] == ["Maria-Angela"]


def test_a_change_of_case_only_keeps_the_file(tmp_path: Path) -> None:
    """`Léo` → `LÉO`: Windows would not tell the two files apart: the file stays."""
    config = _saved(tmp_path, LEO)
    desk, _adopted = _desk(config)
    desk.answer(RenameAsked(name="Léo", to="LÉO"))
    back = read_people(config).person[0]
    assert (back.name, back.file) == ("LÉO", "people/Léo.toml")
    assert (tmp_path / "people" / "Léo.toml").is_file()


def test_an_unknown_name_is_refused(tmp_path: Path) -> None:
    """Nobody of that name: refused, nothing written."""
    desk, _adopted = _desk(_saved(tmp_path, LEO))
    with pytest.raises(ValueError, match="nobody"):
        desk.answer(RenameAsked(name="Zoé", to="Zoe"))


def test_every_setting_naming_the_person_follows(tmp_path: Path) -> None:
    """[slideshow] avoid, [[classify.rules]] and the events files are renamed."""
    config = _saved(tmp_path, ANA, TYPO)
    text = config.read_text() + (
        '\n[slideshow]\navoid = ["Maria-Angela", "maria-angelaela"]  # kept\n'
        '\n[[classify.rules]]\nname = "with her"\nmatch = "person"\n'
        'names = ["Maria-Angelaela", "Léo"]\n'
    )
    config.write_text(text)
    events = tmp_path / "events"
    events.mkdir()
    (events / "2024.toml").write_text(
        '[[rules]]\nname = "x"\nmatch = "person"\nnames = ["MARIA-ANGELAELA"]\n'
    )
    desk, _adopted = _desk(config)
    said = desk.answer(RenameAsked(name=TYPO.name, to=ANA.name))
    written = config.read_text()
    assert 'avoid = ["Maria-Angela"]  # kept' in written
    assert 'names = ["Maria-Angela", "Léo"]' in written
    assert '"Maria-Angela"' in (events / "2024.toml").read_text()
    assert "[slideshow] avoid" in str(said["saved"])
    assert "events/2024.toml" in str(said["saved"])


def test_nothing_to_follow_writes_nothing(tmp_path: Path) -> None:
    """No setting names the person: no file rewritten."""
    config = _saved(tmp_path, LEO)
    before = config.read_text()
    assert not follow_name(config, "Zoé", "Zoe")
    assert config.read_text() == before
