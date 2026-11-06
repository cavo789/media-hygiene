"""The events the tool remembers live in /config/events/<year>.toml (0576)."""

from __future__ import annotations

import dataclasses
import tomllib
from datetime import date, timedelta
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.classify.event_store import add_event, remove_events, replace_event
from media_hygiene.classify.remember_rule import remember_rule
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.classify.rules_edit import remove_rules, replace_rule
from media_hygiene.classify.rules_file import read_rules, read_written
from media_hygiene.cli.config_tidy_flow import show_tidy
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.config.loader import load_settings
from media_hygiene.errors import ConfigError
from media_hygiene.paths.mounts import MountTable
from media_hygiene.search.event_match import Moved
from media_hygiene.search.move_event import remember_event
from tests.support.runtime import make_runtime, output_of

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations

_CONFIG: Final = """# mine
[[classify.rules]]
name = "Films"
match = "kind"
kind = "download"

[[classify.rules]]
name = "Existing folders"
match = "existing_folder"
"""
_TURIN: Final = ClassifyRule(
    name="Turin",
    match=RuleMatch.DATE_RANGE,
    category="Turin",
    dates="2019-07-02..2019-07-04",
)


def _config(folder: Path) -> Path:
    """A config.toml holding two rules."""
    written = folder / "config.toml"
    written.write_text(_CONFIG, encoding="utf-8")
    return written


def test_196_events_leave_config_toml_unchanged(tmp_path: Path) -> None:
    """Every event in events/<year>.toml, in place just above Existing folders."""
    config = _config(tmp_path)
    first = date(2010, 1, 1)
    for number in range(196):
        day = first + timedelta(days=20 * number)
        said = remember_event(config, Moved(f"Event {number}", (day,)))
        assert "is remembered" in said, said
    assert config.read_text(encoding="utf-8") == _CONFIG
    names = [rule.name for rule in read_rules(config)]
    assert len(names) == 198
    assert (names[0], names[-1]) == ("Films", "Existing folders")
    years = sorted(path.name for path in (tmp_path / "events").iterdir())
    assert years[0] == "2010.toml"
    assert len(years) == 11


def test_the_settings_classify_reads_hold_the_events(locations: Locations) -> None:
    """Loaded settings put the events in the rules, defaults kept without a list."""
    config = locations.config_file
    config.write_text("", encoding="utf-8")
    add_event(config, _TURIN)
    rules = load_settings(locations).settings.classify.rules
    assert [rule.name for rule in rules][:3] == [
        "Films and series",
        "Turin",
        "Existing folders",
    ]
    _config(locations.config_dir)
    names = [rule.name for rule in load_settings(locations).settings.classify.rules]
    assert names == ["Films", "Turin", "Existing folders"]


def test_replace_and_remove_in_the_file_holding_the_event(tmp_path: Path) -> None:
    """Changed where it is, even in a file renamed by hand; removed there."""
    config = _config(tmp_path)
    add_event(config, _TURIN)
    (tmp_path / "events" / "2019.toml").rename(tmp_path / "events" / "summer.toml")
    wider = _TURIN.model_copy(update={"dates": "2019-06-30..2019-07-04"})
    assert replace_rule(config, "turin", wider) == wider
    assert "2019-06-30" in (tmp_path / "events" / "summer.toml").read_text("utf-8")
    with pytest.raises(ConfigError):
        replace_event(config, "Nowhere", wider)
    with pytest.raises(ConfigError):
        add_event(config, wider)  # same name
    left = remove_rules(config, ["Turin", "Films"])
    assert [rule.name for rule in left] == ["Existing folders"]
    remove_events(tmp_path, ["Nowhere"])


def test_a_deleted_or_broken_events_file(tmp_path: Path) -> None:
    """Deleted: its events are forgotten. Broken by hand: said, naming the file."""
    config = _config(tmp_path)
    add_event(config, _TURIN)
    events = tmp_path / "events" / "2019.toml"
    events.write_text("[[rules]\n", encoding="utf-8")
    with pytest.raises(ConfigError, match=r"2019\.toml"):
        read_rules(config)
    events.unlink()
    assert len(read_rules(config)) == 2
    (tmp_path / "events" / "not-events.toml").write_text("folders = []\n", "utf-8")
    assert len(read_rules(config)) == 2


def test_a_name_in_both_places_reads_once(tmp_path: Path) -> None:
    """A move cut short: config.toml wins, no duplicate rule."""
    config = _config(tmp_path)
    add_event(config, _TURIN)
    config.write_text(
        _CONFIG + '\n[[classify.rules]]\nname = "TURIN"\nmatch = "date_range"\n'
        'category = "x"\ndates = "2020-01-01..2020-01-02"\n',
        encoding="utf-8",
    )
    assert [rule.name for rule in read_rules(config)].count("TURIN") == 1
    assert "Turin" not in [rule.name for rule in read_rules(config)]


def test_config_tidy_moves_the_events_once(locations: Locations) -> None:
    """Listed read-only, moved with --apply: copy kept, hand rules stay."""
    config = locations.config_file
    hand = '[[classify.rules]]\nname = "Summer"\nmatch = "date_range"\n'
    hand += 'category = "Trips"\ndates = "2018-07-01..2018-07-30"\n\n'
    event = '[[classify.rules]]\nname = "Turin (July 2019)"\nmatch = "date_range"\n'
    event += 'category = "Turin"\ndates = "2019-07-02..2019-07-04"\n\n'
    config.write_text(hand + event + _CONFIG.removeprefix("# mine\n"), "utf-8")
    runtime = dataclasses.replace(
        make_runtime(locations), mounts=MountTable(frozenset())
    )
    show_tidy(runtime, apply=False, dates=False)
    assert "1 event of config.toml moves" in output_of(runtime)
    assert "Turin" in config.read_text("utf-8")
    before = config.read_text("utf-8")
    show_tidy(runtime, apply=True, dates=False)
    assert "1 event moved" in output_of(runtime)
    assert [rule.name for rule in read_written(config)] == [
        "Summer",
        "Films",
        "Existing folders",
    ]
    held = tomllib.loads(
        (locations.config_dir / "events" / "2019.toml").read_text("utf-8")
    )
    assert held["rules"][0]["name"] == "Turin (July 2019)"
    copies = list((locations.cache_dir / "config-backups").iterdir())
    assert [copy.read_text("utf-8") for copy in copies] == [before]
    show_tidy(runtime, apply=True, dates=False)
    assert output_of(runtime).count("event moved") == 1


def test_a_folder_rule_turned_into_dates_moves_to_events(tmp_path: Path) -> None:
    """0611: out of config.toml byte for byte, comments kept; put back on error."""
    config = tmp_path / "config.toml"
    party = '[[classify.rules]]\nname = "Turin"\nmatch = "path"\npattern = "turin"\n\n'
    config.write_text(_CONFIG.replace("# mine\n", f"# mine\n{party}"), encoding="utf-8")
    assert remember_rule(config, "Turin", _TURIN) == _TURIN
    assert config.read_text(encoding="utf-8") == _CONFIG
    assert "Turin" in (tmp_path / "events" / "2019.toml").read_text("utf-8")
    remove_events(tmp_path, ["Turin"])
    config.write_text(_CONFIG.replace("# mine\n", f"# mine\n{party}"), encoding="utf-8")
    before = config.read_bytes()
    taken = _TURIN.model_copy(update={"name": "Films"})
    with pytest.raises(ConfigError):
        remember_rule(config, "Turin", taken)
    assert config.read_bytes() == before
