"""What the cheap producers need, prepared once per run from the settings.

The folder rules are those of `classify` (generic folders of `[keep]` and
`[classify]`, the tool's own band folders), the calendar its `calendar` and
`date_range` rules, the places its `[[classify.places]]`, the generated file names
those of `[keep]` (the keep policy's): one vocabulary for the whole tool.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.bands import band_folders
from media_hygiene.classify.clocks import clocks_of
from media_hygiene.classify.dates import zone_of
from media_hygiene.classify.folders import FolderRules
from media_hygiene.classify.place_match import zones_of
from media_hygiene.classify.rules.calendar import parse_one_off, parse_recurring
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_rules import DEFAULT_RULES
from media_hygiene.plan.name_rules import DEFAULT_NAME_RULES, NameRules

if TYPE_CHECKING:
    from datetime import tzinfo

    from media_hygiene.classify.clocks import Clock
    from media_hygiene.classify.place_match import Zone
    from media_hygiene.classify.rules.calendar import OneOff, Recurring
    from media_hygiene.config.settings import Settings
    from media_hygiene.geo.gazetteer import Gazetteer
    from media_hygiene.tags.normalize import WordRules


@dataclass(frozen=True, slots=True)
class TagContext:  # pylint: disable=too-many-instance-attributes
    """Folder and name rules, calendar, places, towns: all a cheap tag reads."""

    words: WordRules
    folders: FolderRules
    zone: tzinfo  # of the videos' UTC times
    calendar: tuple[tuple[Recurring | OneOff, str], ...]  # the user's date rules
    places: tuple[Zone, ...]
    towns: Gazetteer | None = None  # None: no town named (no GPS position)
    town_km: float = 0.0
    # Names a camera or an app generated (`[keep] generated_names`): they give no word.
    names: NameRules = DEFAULT_NAME_RULES
    clocks: tuple[Clock, ...] = ()  # `[[classify.clocks]]`: cameras set right


def tag_context(settings: Settings, words: WordRules) -> TagContext:
    """Prepare the producers for one run.

    Args:
        settings: Every setting.
        words: Language and stop words of `[tags]`.

    Returns:
        The context, without towns: `with_towns` adds them when a file has GPS.
    """
    classify, keep = settings.classify, settings.keep
    folders = FolderRules.build(
        (*keep.generic_folders, *classify.generic_folders),
        band_folders(classify),
    )
    return TagContext(
        words,
        folders,
        zone_of(classify.timezone),
        _calendar(settings),
        zones_of(classify.places),
        town_km=settings.tags.town_km,
        names=NameRules.from_patterns(keep.generated_names, keep.generic_folders),
        clocks=clocks_of(classify.clocks),
    )


def _calendar(settings: Settings) -> tuple[tuple[Recurring | OneOff, str], ...]:
    """The days the user named in `calendar` and `date_range` rules.

    The built-in Christmas and New Year rules are left out: the vocabulary names
    them already, in the language of the tags.

    Args:
        settings: Every setting.

    Returns:
        Each window and the name of its rule.
    """
    found: list[tuple[Recurring | OneOff, str]] = []
    for rule in settings.classify.rules:
        if rule in DEFAULT_RULES or rule.score == 0:
            continue
        if rule.match is RuleMatch.CALENDAR:
            found.append((parse_recurring(rule.dates), rule.name))
        elif rule.match is RuleMatch.DATE_RANGE:
            found.append((parse_one_off(rule.dates), rule.name))
    return tuple(found)
