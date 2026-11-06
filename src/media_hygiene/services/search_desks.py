"""The desks of the search page built from the runtime: rules, names, events, words."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.classify.own_events import folder_rules
from media_hygiene.search.events_desk import EventsDesk
from media_hygiene.search.found_desk import FoundDesk
from media_hygiene.search.grouping_desk import GroupingPreview
from media_hygiene.search.hand_index import HandIndex
from media_hygiene.search.late_desk import LateDesk
from media_hygiene.search.people_desk import NamesPlace
from media_hygiene.search.rule_desk import RuleDesk
from media_hygiene.search.span_events import SpanEvents
from media_hygiene.search.tag_desk import TagDesk
from media_hygiene.search.tag_drop_desk import DropDesk
from media_hygiene.services.group_sort import sorted_group
from media_hygiene.services.people_page import names_file
from media_hygiene.services.rule_trial import event_gap_hours, try_rule, written_rules
from media_hygiene.services.selection_move import SelectionMover
from media_hygiene.services.sort_event import sorter_of
from media_hygiene.services.sort_reviewing import open_sort_review
from media_hygiene.services.tag_drop import drop_words, merge_word

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.search.chosen_api import ChosenDesk
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.tag_drop import Dropped, Merge


def rule_desk(runtime: Runtime, search: SearchIndex, chosen: ChosenDesk) -> RuleDesk:
    """*Make it a rule* (0396): the date rules of `config.toml`, tried on the index.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.
        chosen: The files set aside, left out of a move (0518).

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
        chosen.paths,
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
    settings = runtime.settings
    names = [person.name for person in settings.people.person]
    found = FoundDesk(
        search.connection,
        runtime.mapper,
        runtime.locations.config_file,
        (folder_rules(settings.classify, names), settings.classify.merge_gap_hours),
    )
    return EventsDesk(
        search,
        runtime.mapper,
        opener,
        chosen.paths,
        partial(sorter_of, runtime),
        found,
        LateDesk(search, runtime.mapper, runtime.locations.config_file, chosen.paths),
        SpanEvents(
            search,
            runtime.mapper,
            chosen.paths,
            event_gap_hours(runtime),
            runtime.locations.config_file.parent,
        ),
        GroupingPreview(
            search.connection,
            runtime.locations.config_file,
            settings.classify.session_gap_hours,
        ),
    )


def tag_desk(runtime: Runtime, search: SearchIndex) -> TagDesk | None:
    """*🏷 Tag…* (0555): the words typed by hand, saved into `/config/tags/`.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.

    Returns:
        The desk; None on a search without words typed by hand (a test's index).
    """
    if not isinstance(search, HandIndex):
        return None
    config = names_file(runtime)
    drop = DropDesk(search, config, partial(_dropping, runtime))
    return TagDesk(search, runtime.mapper, config, drop)


def _dropping(runtime: Runtime, merge: Merge) -> Dropped:
    """Drop the words, or merge the word into its target (0622).

    Args:
        runtime: Settings, mount points and output.
        merge: The words and the tag they mean.

    Returns:
        What was done.
    """
    if merge.target:
        return merge_word(runtime, merge)
    return drop_words(runtime, merge.words)


def shown_roots(runtime: Runtime) -> tuple[Path, ...]:
    """The top folders of the tree: the mounted ones, or the drives of `/data`.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        Them, in the container.
    """
    data_dir = runtime.locations.data_dir
    roots = runtime.mounts.data_roots(data_dir)
    if roots == (data_dir,) and data_dir.is_dir():
        return tuple(sorted(child for child in data_dir.iterdir() if child.is_dir()))
    return roots
