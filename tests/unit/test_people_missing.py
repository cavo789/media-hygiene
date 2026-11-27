"""A linked people file gone: loaded empty, warned, `config tidy` unlinks it (0849)."""

from __future__ import annotations

import dataclasses
import tomllib
from typing import TYPE_CHECKING

from media_hygiene.cli.config_tidy_flow import show_tidy
from media_hygiene.config.loader import load_settings
from media_hygiene.config.people_missing import PEOPLE_LINKS, settings_warning
from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.paths.mounts import MountTable
from media_hygiene.people.config_file import save_people
from media_hygiene.services.config_tidy import stale_entries
from media_hygiene.services.fresh_runtime import FreshRuntime
from tests.support.runtime import make_runtime, output_of

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

CHLOE = Person(name="Chloé", faces=("/a.jpg#0",))
MANON = Person(name="Manon", faces=("/d.jpg#0",))


def _saved(locations: Locations) -> None:
    save_people(locations.config_file, PeopleSettings(person=(CHLOE, MANON)))


def _warning(locations: Locations) -> str:
    return settings_warning(load_settings(locations), locations.config_dir)


def test_a_file_removed_loads_empty_with_one_warning(locations: Locations) -> None:
    """The settings load, the other person keeps their faces, the line names both."""
    _saved(locations)
    assert not _warning(locations)
    (locations.config_dir / "people" / "Chloé.toml").unlink()
    people = load_settings(locations).settings.people.person
    assert [person.faces for person in people] == [(), MANON.faces]
    assert "people/Chloé.toml (Chloé)" in _warning(locations)
    fresh = FreshRuntime(make_runtime(locations))
    assert "people/Chloé.toml" in fresh.error  # the home page's line


def test_a_file_renamed_then_back_again(locations: Locations) -> None:
    """Renamed in Explorer: warned; renamed back: the warning is gone."""
    _saved(locations)
    folder = locations.config_dir / "people"
    (folder / "Chloé.toml").rename(folder / "Chloe-old.toml")
    assert "Chloé" in _warning(locations)
    (folder / "Chloe-old.toml").rename(folder / "Chloé.toml")
    assert not _warning(locations)
    assert load_settings(locations).settings.people.person[0].faces == CHLOE.faces


def test_tidy_lists_it_ticked_and_unlinks_it(locations: Locations) -> None:
    """--apply removes the file line only: the person and the others stay."""
    _saved(locations)
    (locations.config_dir / "people" / "Chloé.toml").unlink()
    runtime = dataclasses.replace(
        make_runtime(locations), mounts=MountTable(frozenset({locations.data_dir}))
    )
    stale = stale_entries(runtime).stale
    assert [(entry.section, entry.rank, entry.ticked) for entry in stale] == [
        (PEOPLE_LINKS, 0, True)
    ]
    show_tidy(runtime, apply=True, opt_in=frozenset())
    people = tomllib.loads(locations.config_file.read_text("utf-8"))["people"]
    assert "file" not in people["person"][0]
    assert people["person"][0]["name"] == "Chloé"
    assert people["person"][1]["file"]
    assert not _warning(locations), output_of(runtime)
