"""`[[classify.rules]]` in config.toml: refused rules name themselves; examples load."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_rules import ClassifyRule, overlapping_ranges
from media_hygiene.config.classify_settings import SCORES, ClassifySettings
from media_hygiene.config.loader import load_settings, write_default_config
from media_hygiene.constants import Locale
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import install

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations


def rules_file(locations: Locations, body: str) -> None:
    """A config.toml holding one rule after `[[classify.rules]]`."""
    locations.config_file.write_text(f"[[classify.rules]]\n{body}\n", "utf-8")


@pytest.mark.parametrize(
    ("body", "said"),
    [
        ('name = "Fair"\nmatch = "path"\npattern = "(?i)kermesse("', "Fair"),
        ('name = "Birthday"\nmatch = "calendar"\ndates = "02-30"', "Birthday"),
        ('name = "Trip"\nmatch = "date_range"\ndates = "2023-13-01"', "Trip"),
        (
            'name = "Xmas"\nmatch = "calendar"\ndates = "12-24"\ncategory = "{y}"',
            "Xmas",
        ),
        (
            'name = "Loop"\nmatch = "path"\npattern = "a"\ncategory = "{category}"',
            "Loop",
        ),
        ('name = "Cam"\nmatch = "camera"', "needs pattern"),
        ('name = "Kind"\nmatch = "kind"', "needs kind"),
        ('name = "Other"\nmatch = "other_category"', "needs category"),
        ('name = "Folders"\nmatch = "existing_folder"\ncategory = "X"', "not used"),
        ('name = "Path"\nmatch = "path"\npattern = "a"\ndates = "12-24"', "not used"),
        ('name = "Bad"\nmatch = "path"\npattern = "a"\ncategory = "a:b"', "Windows"),
        ('match = "path"\npattern = "a"', "name"),
    ],
)
def test_an_invalid_rule_is_refused_with_its_name(
    locations: Locations, body: str, said: str
) -> None:
    """A wrong pattern, date or placeholder, a missing or useless field."""
    rules_file(locations, body)
    with pytest.raises(ConfigError, match=said) as refused:
        load_settings(locations)
    assert "classify.rules.0" in refused.value.message


def test_two_rules_with_one_name_are_refused(locations: Locations) -> None:
    """The name tells the rules apart in the summary."""
    rule = 'name = "Fair"\nmatch = "path"\npattern = "a"\ncategory = "School"'
    rules_file(locations, f"{rule}\n\n[[classify.rules]]\n{rule}")
    with pytest.raises(ConfigError, match="two rules are named 'Fair'"):
        load_settings(locations)


def test_rules_are_not_read_from_the_environment(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An array of tables lives in config.toml only; a variable is ignored."""
    monkeypatch.setenv("MEDIA_HYGIENE_CLASSIFY__RULES", "[]")
    monkeypatch.setenv("MEDIA_HYGIENE_CLASSIFY__LEAVE", '["C:\\\\Albums"]')
    classify = load_settings(locations).settings.classify
    assert classify.rules == ClassifySettings().rules
    assert classify.leave == ("C:\\Albums",)


def test_scores_written_complete_the_default_ones() -> None:
    """A user writing one score keeps the others."""
    settings = ClassifySettings(scores={"calendar": 60})
    assert settings.scores["calendar"] == 60
    assert settings.scores["date-range"] == SCORES["date-range"]


def test_overlapping_date_ranges_are_reported_in_list_order() -> None:
    """Two trips sharing a day: a warning, the first one listed wins."""
    rules = [
        ClassifyRule(name=name, match=RuleMatch.DATE_RANGE, dates=dates, category="X")
        for name, dates in (
            ("Italy", "2023-07-01..2023-07-15"),
            ("Rome", "2023-07-10..2023-07-12"),
            ("Paris", "2023-08-01"),
        )
    ]
    assert overlapping_ranges(rules) == (("Italy", "Rome"),)


def test_the_french_template_adds_saint_nicolas(locations: Locations) -> None:
    """The example calendar is written in the interface language."""
    install(Locale.FR)
    assert write_default_config(locations.config_file, Locale.FR)
    rules = load_settings(locations).settings.classify.rules
    names = [rule.name for rule in rules]
    assert names[-3:] == ["Noël", "Nouvel An", "Saint-Nicolas"]
    christmas = rules[-3]
    assert (christmas.dates, christmas.category) == ("12-24..12-26", "Fêtes/Noël")
    assert rules[0].category == ""  # films and series stay where they are
