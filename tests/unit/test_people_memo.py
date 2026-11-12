"""`[people]` kept between reads, read again after each kind of change of its files."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.people import people_memo
from media_hygiene.people.config_file import read_people, save_people
from media_hygiene.people.people_memo import PeopleMemo, linked_files

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

LEA = Person(name="Léa", faces=("/data/c/a.jpg#0",))
SAME_SIZE = ("/data/c/b.jpg#0",)  # as long as Léa's: an edit that keeps the size


def _saved(tmp_path: Path) -> Path:
    """A `config.toml` linking Léa's file, written as the pages write it."""
    config = tmp_path / "config.toml"
    save_people(config, PeopleSettings(person=(LEA,)))
    return config


def _counting(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    """Count the real parses behind the memo."""
    calls: list[Path] = []

    def counted(config_file: Path) -> PeopleSettings:
        calls.append(config_file)
        return read_people(config_file)

    monkeypatch.setattr(people_memo, "read_people", counted)
    return calls


def _next_tick(reference: Path) -> None:
    """Wait until a write gets another change time than `reference` (coarse clocks)."""
    probe = reference.with_name("probe")
    while True:
        probe.write_bytes(b"x")
        if probe.stat().st_ctime_ns != reference.stat().st_ctime_ns:
            probe.unlink()
            return


def _person_file(config: Path) -> Path:
    (person,) = linked_files(config)
    return person


def test_a_second_read_parses_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Files unchanged: the same settings, one parse."""
    config = _saved(tmp_path)
    calls = _counting(monkeypatch)
    memo = PeopleMemo()
    first = memo.read(config)
    assert memo.read(config) is first
    assert first.person[0].faces == LEA.faces
    assert len(calls) == 1


def _in_place(path: Path) -> None:
    path.write_text(path.read_text("utf-8").replace("a.jpg", "b.jpg"), "utf-8")


def _atomic(path: Path) -> None:
    draft = path.with_name("draft.toml")
    draft.write_text(path.read_text("utf-8").replace("a.jpg", "b.jpg"), "utf-8")
    draft.replace(path)


def _copy_keeping_mtime(path: Path) -> None:
    before = path.stat()
    _in_place(path)
    os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))


def _touched(path: Path) -> None:
    os.utime(path)


@pytest.mark.parametrize(
    "change",
    [_in_place, _atomic, _copy_keeping_mtime, _touched],
    ids=lambda f: f.__name__,
)
def test_each_change_of_a_person_file_is_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: Callable[[Path], None]
) -> None:
    """An edit in place, an atomic save, a copy keeping the time, a touch: read anew."""
    config = _saved(tmp_path)
    calls = _counting(monkeypatch)
    memo = PeopleMemo()
    memo.read(config)
    person = _person_file(config)
    _next_tick(person)
    change(person)
    after = memo.read(config)
    assert len(calls) == 2
    if change is not _touched:
        assert after.person[0].faces == SAME_SIZE


def test_a_person_added_in_config_toml_is_seen(tmp_path: Path) -> None:
    """A save of the pages (config.toml and a new file): the new person is there."""
    config = _saved(tmp_path)
    memo = PeopleMemo()
    memo.read(config)
    paul = Person(name="Paul", faces=("/data/c/p.jpg#0",))
    save_people(config, PeopleSettings(person=(LEA, paul)))
    assert [each.name for each in memo.read(config).person] == ["Léa", "Paul"]


def test_a_missing_person_file_raises_and_nothing_is_kept(tmp_path: Path) -> None:
    """The file of a person removed: the read says so; restored, it is read again."""
    config = _saved(tmp_path)
    memo = PeopleMemo()
    memo.read(config)
    person = _person_file(config)
    text = person.read_text("utf-8")
    person.unlink()
    with pytest.raises(ValueError, match="is missing"):
        memo.read(config)
    person.write_text(text, "utf-8")
    assert memo.read(config).person[0].faces == LEA.faces


def test_no_config_toml_then_one(tmp_path: Path) -> None:
    """No file: no name; the file written later is read."""
    config = tmp_path / "config.toml"
    memo = PeopleMemo()
    assert memo.read(config) == PeopleSettings()
    save_people(config, PeopleSettings(person=(LEA,)))
    assert memo.read(config).person[0].name == "Léa"


def test_links_outside_the_folder_or_unreadable_toml_are_left_to_the_read(
    tmp_path: Path,
) -> None:
    """`linked_files` lists what it can; the read that follows reports the rest."""
    config = tmp_path / "config.toml"
    config.write_text('[[people.person]]\nname = "X"\nfile = "../out.toml"\n', "utf-8")
    assert not linked_files(config)
    config.write_text("[people\n", "utf-8")
    assert not linked_files(config)
    config.write_text("people = 3\n", "utf-8")
    assert not linked_files(config)
