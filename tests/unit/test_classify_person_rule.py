"""The `person` rule: events with someone named, by share; lone files; unknown names."""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from media_hygiene.classify.engine import Classification, Scope, classify
from media_hygiene.classify.models import Band, MediaInput, Proposal, SortReason
from media_hygiene.classify.rules.building import Seen
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.config.settings import Settings
from media_hygiene.errors import ConfigError, MountError
from media_hygiene.scan.models import VisualFacts
from media_hygiene.services.classify_people import check_people, with_people
from tests.support.layouts import legacy
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.paths.locations import Locations

ROOT = Path("/data/c/Photos")
START = datetime(2023, 5, 1, 10)


def rule(*names: str, **fields: object) -> ClassifyRule:
    """A `person` rule giving `People/<first name>`."""
    return ClassifyRule.model_validate(
        {
            "name": f"With {names[0]}",
            "match": RuleMatch.PERSON,
            "names": names,
            "category": f"People/{names[0]}",
            **fields,
        }
    )


def event(count: int, start: datetime = START) -> list[MediaInput]:
    """`count` photos, ten minutes apart: one event."""
    files = []
    for index in range(count):
        taken = (start + timedelta(minutes=10 * index)).strftime("%Y:%m:%d %H:%M:%S")
        visual = VisualFacts(0, 0, 4000, 3000, 0.0, taken, "Pixel")
        files.append(
            MediaInput(ROOT / f"DCIM/{start:%m%d}_{index}.jpg", ROOT, 1, 0, visual)
        )
    return files


def run(
    files: list[MediaInput],
    people: Mapping[Path, tuple[str, ...]],
    *rules: ClassifyRule,
) -> dict[str, Proposal]:
    """Classify with these rules and these people on the photos, by file name."""
    found: Classification = classify(
        files, legacy(rules=rules), Scope(seen=Seen(people=people))
    )
    return {p.file.path.name: p for p in found.proposals}


def test_an_event_with_someone_on_a_tenth_of_it_takes_the_rule() -> None:
    """One photo of Chloé in ten: the whole event is hers, sure, named by the rule."""
    files = event(10)
    found = run(files, {files[3].path: ("Chloé",)}, rule("chloe"))
    assert {p.folder for p in found.values()} == {"2023/People/chloe"}
    first = next(iter(found.values()))
    assert (first.band, first.reason, first.rule) == (
        Band.SURE,
        SortReason.PERSON,
        "With chloe",
    )


def test_below_the_share_the_event_is_left_to_other_rules() -> None:
    """One photo in twenty is 5 %: not enough by default, enough with min_share = 5."""
    files = event(20)
    people = {files[0].path: ("Chloé",)}
    assert all(p.rule == "" for p in run(files, people, rule("Chloé")).values())
    lowered = run(files, people, rule("Chloé", min_share=5))
    assert all(p.rule == "With Chloé" for p in lowered.values())


def test_any_name_or_every_name() -> None:
    """Any of the names by default; with `all`, each one on its share of photos."""
    files = event(10)
    chloe = {files[0].path: ("Chloé",)}
    assert run(files, chloe, rule("Manon", "Chloé"))[files[5].path.name].rule
    both = rule("Manon", "Chloé", all=True)
    assert not run(files, chloe, both)[files[5].path.name].rule
    together = {**chloe, files[9].path: ("Manon", "Léa")}
    assert run(files, together, both)[files[5].path.name].rule == "With Manon"


def test_a_file_outside_any_event_is_read_alone() -> None:
    """Two lone photos, months apart: only the one showing her goes."""
    lone = [*event(1), *event(1, datetime(2023, 9, 1))]
    found = run(lone, {lone[0].path: ("Chloé",)}, rule("Chloé"))
    assert found[lone[0].path.name].reason is SortReason.PERSON
    assert found[lone[1].path.name].reason is not SortReason.PERSON


@pytest.mark.parametrize(
    ("people", "said"),
    [
        (
            (Person(name="Chloé", faces=("/a#0",)),),
            (
                "Rule 'With Manon': nobody is named \"Manon\" in [[people.person]]. "
                "Named: Chloé."
            ),
        ),
        ((), "Nobody is named yet."),
    ],
)
def test_a_rule_naming_nobody_is_refused_with_its_name(
    people: tuple[Person, ...], said: str
) -> None:
    """The rule and the unknown name are said, with who is named."""
    settings = Settings(
        classify=legacy(rules=(rule("Manon"),)),
        people=PeopleSettings(person=people),
    )
    with pytest.raises(ConfigError) as refused:
        check_people(settings)
    assert said in refused.value.message
    assert refused.value.tip is not None
    assert "'people' page" in refused.value.tip


def test_names_are_checked_without_case_nor_accents() -> None:
    """`CHLOE` is Chloé; without a person rule, nothing is checked nor read."""
    named = PeopleSettings(person=(Person(name="Chloé", faces=("/a#0",)),))
    settings = Settings(classify=legacy(rules=(rule("CHLOE"),)), people=named)
    assert check_people(settings)
    assert not check_people(Settings())


def test_the_index_is_read_only_for_a_person_rule(locations: Locations) -> None:
    """No rule or no index: the scope as it was; an unreadable index: said."""
    assert with_people(Scope(), make_runtime(locations)).seen.people == {}
    locations.config_file.write_text(
        '[[classify.rules]]\nname = "Kids"\nmatch = "person"\nnames = ["Léa"]\n'
        '\n[[people.person]]\nname = "Léa"\nfaces = ["/a#0"]\n',
        "utf-8",
    )
    runtime = make_runtime(locations)
    assert with_people(Scope(), runtime).seen.people == {}
    locations.index_file.write_bytes(b"not an index" * 100)
    with pytest.raises(MountError, match="cannot be read"):
        with_people(Scope(), runtime)
