"""The app of `search` and `browse`: for their own server, or the home's (0356).

Both read the index; the files set aside on either are written into `decisions.json`
of the reports folder, checked writable before each save, for `clean --decisions`.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.apply_api import APPLY_PATH, ApplyDesk, ApplyOffer
from media_hygiene.review.page_header import headed_page
from media_hygiene.search.app import (
    SEARCH_PAGE_PATH,
    SEARCH_PATH,
    SearchApp,
    SearchPages,
)
from media_hygiene.search.chosen_api import CHOSEN_PATH, ChosenDesk
from media_hygiene.search.folders import (
    BROWSE_PATH,
    FOLDER_PATH,
    FOLDERS_PATH,
    FolderDesk,
)
from media_hygiene.search.heaviest import FIRST_SHOWN, HEAVIEST_PATH
from media_hygiene.search.people_desk import PEOPLE_REJECT_PATH, NamesPlace, PeopleDesk
from media_hygiene.search.people_why import PEOPLE_WHY_PATH
from media_hygiene.search.place import SearchPlace
from media_hygiene.search.rule_desk import (
    PERIOD_RULES_PATH,
    RULE_SAVE_PATH,
    RULE_TRIAL_PATH,
    RuleDesk,
)
from media_hygiene.search.rule_go import RULE_GO_PATH
from media_hygiene.services.albums import album_desk
from media_hygiene.services.chosen_place import chosen_store, reports_ready
from media_hygiene.services.group_sort import sorted_group
from media_hygiene.services.people_page import names_file
from media_hygiene.services.rule_trial import try_rule, written_rules
from media_hygiene.share.album_api import ALBUMS_PATH
from media_hygiene.share.album_pickers import SearchPicker

if TYPE_CHECKING:
    from collections.abc import Callable
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.review.apply_api import ApplyStep
    from media_hygiene.review.ending import Ending
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.runtime import Runtime

_PACKAGE: Final = "media_hygiene.search"
_SEARCH_TEMPLATE: Final = "search.html.j2"
_BROWSE_TEMPLATE: Final = "browse.html.j2"


@dataclass(frozen=True, slots=True)
class SearchBuild:
    """What the app needs from its server: `/` and *Apply now*, its end, its pool."""

    first: str  # the page `/` serves: `/search` or `/browse`
    apply: Callable[[], ApplyStep | None] | None  # None: no *Apply now*
    ending: Ending
    executor: Executor


def search_app(runtime: Runtime, search: SearchIndex, build: SearchBuild) -> SearchApp:
    """Build the search page and the folder view on an open index.

    Args:
        runtime: Settings, mount points and output.
        search: The open index, owned by the caller.
        build: The server's end, pool, first page and *Apply now*.

    Returns:
        The app, answering both pages and their API.
    """
    environment = translated_environment(_PACKAGE, escaped=("html", "j2"))
    paths = {
        "search_path": SEARCH_PATH,
        "chosen_path": CHOSEN_PATH,
        "browse_path": BROWSE_PATH,
        "search_page": SEARCH_PAGE_PATH,
        "folders_path": FOLDERS_PATH,
        "folder_path": FOLDER_PATH,
        "heaviest_path": HEAVIEST_PATH,
        "heaviest_first": FIRST_SHOWN,
        "apply_path": APPLY_PATH,
        "albums_path": ALBUMS_PATH,
        "people_reject_path": PEOPLE_REJECT_PATH,
        "people_why_path": PEOPLE_WHY_PATH,
        "rule_trial_path": RULE_TRIAL_PATH,
        "rule_save_path": RULE_SAVE_PATH,
        "period_rules_path": PERIOD_RULES_PATH,
        "rule_go_path": RULE_GO_PATH,
        "event_gap_hours": event_gap_hours(runtime),
        "apply_offered": build.apply is not None,
    }
    pages = SearchPages(
        headed_page(environment, _SEARCH_TEMPLATE, paths),
        headed_page(environment, _BROWSE_TEMPLATE, paths),
        build.first,
    )
    chosen = chosen_desk(runtime, search)
    folders = FolderDesk(search, runtime.mapper, shown_roots(runtime), chosen)
    place = SearchPlace(
        search,
        runtime.mapper,
        runtime.previews_dir,
        runtime.settings.people,
        chosen,
        folders,
        ApplyDesk(ApplyOffer(build.apply, lambda: bool(chosen.paths())), build.ending),
        album_desk(runtime, SearchPicker(search).files),
        PeopleDesk(search, names_place(runtime)),
        rule_desk(runtime, search),
    )
    return SearchApp(place, pages, build.executor)


def event_gap_hours(runtime: Runtime) -> float:
    """The longest gap between two photos of one event, as `classify` groups them.

    Args:
        runtime: Settings.

    Returns:
        Hours: the larger of `session_gap_hours` and `merge_gap_hours`.
    """
    classify = runtime.settings.classify
    return max(classify.session_gap_hours, classify.merge_gap_hours)


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
    )


def names_place(runtime: Runtime) -> NamesPlace:
    """Where the page saves the names it corrects, and `[people]` at the start.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The place; no file when `/config` cannot be written.
    """
    return NamesPlace(names_file(runtime), runtime.settings.people, runtime.mapper)


def chosen_desk(runtime: Runtime, search: SearchIndex) -> ChosenDesk:
    """The files set aside from the pages: `decisions.json` in the reports folder.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.

    Returns:
        The desk answering the pages about them.
    """
    return ChosenDesk(chosen_store(runtime), search, partial(reports_ready, runtime))


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
