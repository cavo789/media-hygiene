"""The desks of the search page built from the runtime: rules, names, events."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.search.events_desk import EventsDesk
from media_hygiene.search.people_desk import NamesPlace
from media_hygiene.search.rule_desk import RuleDesk
from media_hygiene.services.group_sort import sorted_group
from media_hygiene.services.people_page import names_file
from media_hygiene.services.rule_trial import try_rule, written_rules
from media_hygiene.services.selection_move import SelectionMover
from media_hygiene.services.sort_reviewing import open_sort_review

if TYPE_CHECKING:
    from media_hygiene.search.chosen_api import ChosenDesk
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.runtime import Runtime


def rule_desk(runtime: Runtime, search: SearchIndex) -> RuleDesk:
    """*Make it a rule* (0396): the date rules of `config.toml`, tried on the index.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.

    Returns:
        The desk.
    """
    return RuleDesk(
        search,
        runtime.mapper,
        runtime.locations.config_file,
        partial(written_rules, runtime),
        partial(try_rule, runtime, search.connection),
        partial(sorted_group, runtime),
        SelectionMover(runtime),
    )


def names_place(runtime: Runtime) -> NamesPlace:
    """Where the page saves the names it corrects, and `[people]` at the start.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The place; no file when `/config` cannot be written.
    """
    return NamesPlace(names_file(runtime), runtime.settings.people, runtime.mapper)


def events_desk(
    runtime: Runtime, search: SearchIndex, chosen: ChosenDesk
) -> EventsDesk:
    """The *🗂 Events* view (0437): the latest classify plan, read on the first ask.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.
        chosen: The files set aside, marked on the tiles.

    Returns:
        The desk.
    """
    opener = partial(open_sort_review, runtime, None)
    return EventsDesk(search, runtime.mapper, opener, chosen.paths)
