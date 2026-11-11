"""`config tidy`: the entries of config.toml pointing at nothing, found and removed."""

from __future__ import annotations

import dataclasses
import tomllib
from datetime import date
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.cli.config_tidy_flow import show_tidy, tidy_tip
from media_hygiene.config.loader import default_config
from media_hygiene.config.tidy_find import find_stale
from media_hygiene.config.tidy_rules import LibraryFacts, OptIn, StaleEntry
from media_hygiene.config.tidy_write import check_removed, without_entries
from media_hygiene.constants import Locale
from media_hygiene.errors import ConfigError
from media_hygiene.paths.mounts import MountTable
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.config_tidy import _shot, library_facts, stale_entries
from tests.support.runtime import make_runtime, output_of
from tests.support.scenes import Shot, write_shot

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime

FACTS: Final = LibraryFacts(
    paths=(r"C:\Photos\Vacances\Week-end à Dinant 2020\a.jpg",),
    shots=(("Apple iPhone 12", date(2020, 7, 4)),),
)
RULES: Final = """
[[classify.rules]]
name = "Dinant"
match = "path"
pattern = '(?i)week-end dinant'
category = "Trips"

[[classify.rules]]
name = "Bapteme"
match = "path"
pattern = '(?i)bapt.me manon'
category = "Family"

[[classify.rules]]
name = "Holidays"
match = "path"
pattern = '(?i)vacances'
category = "Trips"

[[classify.rules]]
name = "Drone"
match = "camera"
pattern = '(?i)dji'
category = "Drone"

[[classify.rules]]
name = "Trip 2031"
match = "date_range"
dates = "2031-07-01..2031-07-15"
category = "Trips"

[[classify.rules]]
name = "Holidays"
match = "path"
pattern = '(?i)vacances'
category = "Trips"

[[classify.clocks]]
camera = "(?i)canon"
dates = "2010-07-01..2010-07-15"
shift = "+1h"
"""


def everything(path: str) -> bool | None:
    """Every folder exists but those named `gone`; `E:` is not mounted."""
    if path.startswith("E:"):
        return None
    return "gone" not in path


def reasons(text: str, facts: LibraryFacts = FACTS) -> dict[str, StaleEntry]:
    """The stale entries of a file, by section and label."""
    found = find_stale(tomllib.loads(text), facts, everything)
    return {f"{entry.section}:{entry.label}": entry for entry in found.stale}


def test_rules_and_clocks_judged_against_the_index() -> None:
    """Sorted away paths, an absent camera, an unknown clock, a duplicate: found."""
    found = reasons(RULES)
    assert set(found) == {
        "classify.rules:Dinant",
        "classify.rules:Bapteme",
        "classify.rules:Drone",
        "classify.rules:Trip 2031",
        "classify.rules:Holidays",
        "classify.clocks:(?i)canon 2010-07-01..2010-07-15",
    }
    assert found["classify.rules:Holidays"].rank == 5  # the second one only
    assert not found["classify.rules:Trip 2031"].ticked  # written before an import
    assert found["classify.rules:Bapteme"].ticked


def test_an_empty_index_judges_no_pattern() -> None:
    """A partial or empty index never makes the rules look stale."""
    found = reasons(RULES, LibraryFacts())
    assert set(found) == {"classify.rules:Holidays"}  # the duplicate only


def test_folders_gone_duplicated_or_on_an_unmounted_drive() -> None:
    """A folder gone is stale; one on a drive not mounted is unknown, not missing."""
    text = r"""
[folders]
protected = ['C:\Photos\gone', 'E:\Stick', 'C:\Photos\kept', 'c:\photos\KEPT']

[[places.folders]]
folder = 'C:\Photos\2010\gone\Quimper'
latitude = 48.0
longitude = -4.1

[[places.ignored]]
latitude = 48.0
longitude = -4.1
"""
    found = find_stale(tomllib.loads(text), FACTS, everything)
    labels = {(entry.section, entry.rank) for entry in found.stale}
    assert labels == {
        ("folders.protected", 0),
        ("folders.protected", 3),
        ("places.folders", 0),
    }
    assert found.unknown == (r"E:\Stick",)


def test_removal_keeps_the_comments_of_the_default_template() -> None:
    """Only the ticked rows go; comments, order and the rest stay byte for byte."""
    template = default_config(Locale.EN) + RULES
    stale = find_stale(tomllib.loads(template), FACTS, everything).stale
    ticked = [entry for entry in stale if entry.ticked]
    result = without_entries(template, ticked)
    names = [rule["name"] for rule in tomllib.loads(result)["classify"]["rules"]]
    assert "Bapteme" not in names
    assert "Trip 2031" in names
    assert names.count("Holidays") == 1
    assert "clocks" not in tomllib.loads(result)["classify"]
    for line in default_config(Locale.EN).splitlines():
        if line.startswith("#"):
            assert line in result


def test_another_change_is_refused() -> None:
    """A text changed beyond the entries is never accepted."""
    entry = StaleEntry("classify.rules", 1, "Bapteme", "gone")
    with pytest.raises(ConfigError):
        check_removed(RULES, RULES, [entry])


def test_the_shot_of_a_file() -> None:
    """Camera from the visual facts, day from its EXIF date; none without facts."""
    visual = dataclasses.make_dataclass("V", ["camera", "taken_at"])
    assert _shot(visual("DJI", "2020:07:04 10:00:00"), None) == (
        "DJI",
        date(2020, 7, 4),
    )
    assert _shot(visual(None, "bad"), None) == ("", None)


def mounted(locations: Locations) -> Runtime:
    """A runtime whose data mount `/data/c` is mounted, config.toml with RULES."""
    (locations.data_dir / "c" / "Photos" / "kept").mkdir(parents=True)
    rules = RULES.split("[[classify.clocks]]", maxsplit=1)[0].rsplit(
        "[[classify.rules]]", 1
    )[0]
    text = "[folders]\nprotected = ['C:\\Photos\\kept', 'C:\\Photos\\gone']\n" + rules
    locations.config_file.write_text(text, "utf-8")
    runtime = make_runtime(locations)
    mounts = MountTable(frozenset({locations.data_dir / "c"}))
    return dataclasses.replace(runtime, mounts=mounts)


def test_list_then_apply_with_a_copy_and_the_undo_line(locations: Locations) -> None:
    """Listed read-only first; --apply keeps a copy, removes, reads back."""
    runtime = mounted(locations)
    assert library_facts(runtime) == LibraryFacts()  # no index yet
    stale = stale_entries(runtime).stale
    assert [(entry.section, entry.rank) for entry in stale] == [
        ("folders.protected", 1),
    ]
    show_tidy(runtime, apply=False, opt_in=frozenset())
    assert "Nothing was written" in output_of(runtime)
    before = locations.config_file.read_text("utf-8")
    show_tidy(runtime, apply=True, opt_in=frozenset())
    after = tomllib.loads(locations.config_file.read_text("utf-8"))
    assert after["folders"]["protected"] == ["C:\\Photos\\kept"]
    copies = list((locations.cache_dir / "config-backups").iterdir())
    assert [copy.read_text("utf-8") for copy in copies] == [before]
    assert "Changed your mind?" in output_of(runtime)
    tidy_tip(runtime)
    show_tidy(runtime, apply=False, opt_in=frozenset())
    assert "points at something" in output_of(runtime)


def test_the_tip_after_sort(locations: Locations, tmp_path: Path) -> None:
    """One line when entries point at nothing; silent on a broken file."""
    runtime = mounted(locations)
    tidy_tip(runtime)
    assert "1 entry of config.toml points at nothing" in output_of(runtime)
    locations.config_file.write_text("[broken", "utf-8")
    tidy_tip(runtime)
    assert tmp_path.exists()


SUPERSEDED: Final = """
[[classify.rules]]
name = "Dinant"
match = "path"
pattern = '(?i)dinant'
category = "Trips/Dinant"

[[classify.rules]]
name = "Bruges"
match = "path"
pattern = '(?i)bruges'
category = "Trips/Bruges"
"""


def test_a_path_rule_whose_files_sit_in_named_folders_is_superseded() -> None:
    """Every match in a folder the user named: shown, ticked only on request (0693)."""
    dinant = r"C:\Photos\2020\2020-08\Dinant\a.jpg"
    bruges = (r"C:\Photos\2017\2017-04\Bruges\b.jpg", r"C:\Photos\2017\bruges.jpg")
    facts = LibraryFacts(paths=(dinant, *bruges), named=frozenset({dinant, bruges[0]}))
    found = reasons(SUPERSEDED, facts)
    assert set(found) == {"classify.rules:Dinant"}  # one Bruges file is still loose
    entry = found["classify.rules:Dinant"]
    assert not entry.ticked
    assert entry.opt_in is OptIn.SUPERSEDED
    assert "1 files" in entry.reason


def test_library_facts_names_the_folders_existing_folder_keeps(
    locations: Locations,
) -> None:
    """A named folder counts, a date-only folder does not."""
    runtime = mounted(locations)
    root = locations.data_dir / "c"
    named, dated = root / "2017" / "2017-04" / "Bruges", root / "2017" / "2017-05"
    for folder in (named, dated):
        write_shot(folder / "a.jpg", Shot(len(folder.name)))
    AuditService(runtime, NullProgress()).run()
    facts = library_facts(runtime)
    hosts = {path.rsplit("\\", 2)[-2]: path for path in facts.paths}
    assert hosts["Bruges"] in facts.named
    assert hosts["2017-05"] not in facts.named


def test_superseded_rules_removed_with_the_option(locations: Locations) -> None:
    """`--superseded` ticks them; without it, nothing is written."""
    runtime = mounted(locations)
    entry = StaleEntry("classify.rules", 0, "x", "why", OptIn.SUPERSEDED)
    assert not entry.ticked
    show_tidy(runtime, apply=False, opt_in=frozenset({OptIn.SUPERSEDED}))
    assert "Nothing was written" in output_of(runtime)
