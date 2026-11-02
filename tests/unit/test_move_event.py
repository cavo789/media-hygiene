"""The event *Move to an event…* remembers: name, period, cameras (0556)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import date
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

from media_hygiene.classify.event_files import (
    add_not_events,
    add_refused,
    read_not_events,
    read_refused,
)
from media_hygiene.classify.event_folder import event_folder
from media_hygiene.classify.rules.calendar import overlapping_ranges, parse_one_off
from media_hygiene.classify.rules.devices import devices_test, to_ask
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.classify.rules_file import read_rules
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.review.rule_overlaps import overlapping
from media_hygiene.search.event_match import Moved, label
from media_hygiene.search.move_event import foreseen, remember_event

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput

_CONFIG = """# mine
[[classify.rules]]
name = "Existing folders"
match = "existing_folder"
"""
_PHONE = ("Apple iPhone 12",)


def _config(tmp_path: Path) -> Path:
    """A config.toml holding one rule."""
    written = tmp_path / "config.toml"
    written.write_text(_CONFIG, encoding="utf-8")
    return written


def _events(config: Path) -> list[ClassifyRule]:
    """The events the file holds."""
    return [rule for rule in read_rules(config) if rule.match is RuleMatch.DATE_RANGE]


def test_a_move_writes_the_event_and_reads_it_back(tmp_path: Path) -> None:
    """The name, the days and the cameras: comments kept."""
    config = _config(tmp_path)
    moved = Moved("Turin", (date(2019, 7, 2), date(2019, 7, 4)), _PHONE)
    assert "'Turin'" in foreseen(config, moved)
    said = remember_event(config, moved)
    assert "2019-07-02..2019-07-04" in said
    assert "Apple iPhone 12" in said
    (event,) = _events(config)
    assert (event.name, event.category, event.devices) == ("Turin", "Turin", _PHONE)
    assert config.read_text(encoding="utf-8").startswith("# mine")


def test_two_turin_events_each_with_its_late_photo(tmp_path: Path) -> None:
    """A move to Turin joins the Turin of its days, else starts another one."""
    config = _config(tmp_path)
    remember_event(config, Moved("Turin", (date(2019, 7, 2),), _PHONE))
    later = Moved("Turin", (date(2022, 4, 1),))
    assert "Turin (July 2019)" in foreseen(config, later)
    assert "Turin (April 2022)" in remember_event(config, later)
    late = Moved("Turin", (date(2019, 7, 3),), ("Canon EOS",))
    assert "Turin (July 2019)" in foreseen(config, late)
    remember_event(config, late)
    remember_event(config, Moved("Turin", (date(2022, 4, 2),)))
    events = {rule.name: (rule.dates, rule.devices) for rule in _events(config)}
    assert events == {
        "Turin": ("2019-07-02..2019-07-03", ("Apple iPhone 12", "Canon EOS")),
        "Turin (April 2022)": ("2022-04-01..2022-04-02", ()),
    }
    rules = read_rules(config)
    assert [label(rule, rules) for rule in _events(config)] == [
        "Turin (July 2019)",
        "Turin (April 2022)",
    ]


def test_no_date_remembers_nothing(tmp_path: Path) -> None:
    """Files without a date: no event."""
    config = _config(tmp_path)
    assert not remember_event(config, Moved("Turin", (), _PHONE))
    assert not foreseen(config, Moved("Turin", (), _PHONE))
    assert len(read_rules(config)) == 1


def test_a_file_without_rules_list_says_why(tmp_path: Path) -> None:
    """No [[classify.rules]]: the move ran, the event is not remembered, said."""
    config = tmp_path / "config.toml"
    config.write_text("", encoding="utf-8")
    said = remember_event(config, Moved("Turin", (date(2019, 7, 2),)))
    assert "not remembered" in said


def test_refusals_go_to_their_own_file_only_when_there_is_one(tmp_path: Path) -> None:
    """Created and linked on the first refusal, read back, by content id."""
    config = _config(tmp_path)
    remember_event(config, Moved("Turin", (date(2019, 7, 2),), _PHONE))
    (event,) = _events(config)
    assert not read_refused(tmp_path, event)
    assert add_refused(config, event, ()) == frozenset()
    assert not (tmp_path / "events").exists()
    assert add_refused(config, event, ("aa", "bb")) == {"aa", "bb"}
    (linked,) = _events(config)
    assert linked.file == "events/2019-07-02-Turin.toml"
    assert add_refused(config, linked, ("cc",)) == {"aa", "bb", "cc"}
    assert read_refused(tmp_path, _events(config)[0]) == {"aa", "bb", "cc"}


def test_folders_of_no_event_are_kept_by_content_id(tmp_path: Path) -> None:
    """`events/not-events.toml`, created on the first answer (0557)."""
    assert not read_not_events(tmp_path)
    assert add_not_events(tmp_path, ("aa",)) == {"aa"}
    assert add_not_events(tmp_path, ("bb", "aa")) == {"aa", "bb"}


def _index(rows: list[tuple[str, str, str | None]]) -> sqlite3.Connection:
    """An index holding the columns the folder search reads."""
    connection = sqlite3.connect(":memory:")
    connection.execute("CREATE TABLE files (path TEXT, media_date TEXT, camera TEXT)")
    connection.executemany("INSERT INTO files VALUES (?, ?, ?)", rows)
    return connection


def test_an_event_folder_renamed_in_explorer_is_found_again() -> None:
    """Its files of its days and cameras: their folder now; another camera's is not."""
    event = _event("Turin", _PHONE)
    moved = "/data/c/Photos/2023/2023-04/Turin"
    with closing(
        _index(
            [
                (
                    "/data/c/Photos/2023/2023-04/Turin with Anna/a.jpg",
                    "2023:04:01 10:00:00",
                    _PHONE[0],
                ),
                (
                    "/data/c/Photos/2023/2023-04/Turin with Anna/b.jpg",
                    "2023:04:02 10:00:00",
                    _PHONE[0],
                ),
                (
                    "/data/c/Photos/2023/2023-04/Hers/c.jpg",
                    "2023:04:02 10:00:00",
                    "Samsung S21",
                ),
                (
                    "/data/c/Photos/2023/2023-04/Hers/d.jpg",
                    "2023:04:02 11:00:00",
                    "Samsung S21",
                ),
                (
                    "/data/c/Photos/2023/2023-04/Hers/e.jpg",
                    "2023:04:02 12:00:00",
                    "Samsung S21",
                ),
                ("/data/c/Photos/x.jpg", "not a date", None),
            ]
        )
    ) as connection:
        assert event_folder(connection, event, moved) == (
            "/data/c/Photos/2023/2023-04/Turin with Anna"
        )
        connection.execute(
            "UPDATE files SET path = replace(path, 'Turin with Anna', 'Turin')"
        )
        assert event_folder(connection, event, moved) == moved
    with closing(_index([])) as empty:
        assert event_folder(empty, event, moved) is None


def _event(name: str, devices: tuple[str, ...]) -> ClassifyRule:
    """An event of 1-3 April 2023."""
    return ClassifyRule(
        name=name,
        match=RuleMatch.DATE_RANGE,
        category=name,
        dates="2023-04-01..2023-04-03",
        devices=devices,
    )


def test_events_of_other_cameras_share_their_days() -> None:
    """Same days, other cameras: no clash; a shared camera or none still clashes."""
    mine, hers = _event("Mine", _PHONE), _event("Hers", ("Samsung S21",))
    assert not overlapping_ranges((mine, hers))
    assert overlapping_ranges((mine, _event("Any", ()))) == (("Mine", "Any"),)
    window = parse_one_off("2023-04-02")
    assert overlapping(window, (mine, hers), _PHONE) == [
        "Mine (2023-04-01..2023-04-03)"
    ]
    assert len(overlapping(window, (mine, hers))) == 2


def test_a_file_of_another_camera_is_not_the_event_s() -> None:
    """The event's cameras narrow its days; a file without camera is to be asked."""
    test = devices_test(_PHONE, lambda _file: True)
    asked = to_ask(_PHONE, lambda _file: True)

    def file(camera: str | None) -> MediaInput:
        return cast("MediaInput", SimpleNamespace(camera=camera))

    assert test(file("apple iphone 12"))
    assert not test(file("Samsung S21"))
    assert not test(file(None))
    assert asked(file(None))
    assert not asked(file("Samsung S21"))
    assert not to_ask((), lambda _file: True)(file(None))
    assert devices_test((), lambda _file: True)(file(None))
