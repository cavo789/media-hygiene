"""The library kept when only faces were named, its names read again (2026-11-16).

Each naming on `/person` changes `/config/people/*.toml`, so the home server's
settings change, and the library was built again: its index opened again, search
by meaning loaded again, its full-text table rebuilt at the next search (1 s, then
3.3 s, measured on the maintainer's PC). When the settings differ by the faces of
people already known only — the same names, every other setting equal — the library
stays: the names of the photos are read again for the search (`NamesKept`, in a
thread), and the people desk forgets the faces it had read. A new person, a name
changed or any other setting builds the library again, as before: the Events view
reads the people's names for its folder rules.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.review.apply_relay import home_relay
from media_hygiene.review.slow_log import Laps
from media_hygiene.search.app import SEARCH_PAGE_PATH
from media_hygiene.search.meaning_index import MeaningIndex
from media_hygiene.search.names_soon import NamesKept
from media_hygiene.services.search_app import SearchBuild, search_app

if TYPE_CHECKING:
    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.search.app import SearchApp
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.home_pages import HomeServer
    from media_hygiene.services.runtime import Runtime


def built_library(
    runtime: Runtime, search: SearchIndex, server: HomeServer
) -> SearchApp:
    """Build the library on an open index; said in the console when slow.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.
        server: The home server's *Apply now*, end, pool and TV.

    Returns:
        The library.
    """
    laps = Laps("library built")
    relay = home_relay(runtime.locations.reports_dir)
    s = server
    build = SearchBuild(SEARCH_PAGE_PATH, s.apply, s.ending, s.executor, relay, s.tv)
    app = search_app(runtime, search, build)
    laps.lap("desks")
    laps.said()
    return app


def faces_only(before: Runtime, after: Runtime) -> bool:
    """Whether two settings differ by the faces of the people already named only.

    Args:
        before: The runtime the library was built for.
        after: The runtime now.

    Returns:
        True when every other setting and every name are the same.
    """
    old, new = before.settings, after.settings
    if old.model_copy(update={"people": new.people}) != new:
        return False
    return _names(old.people) == _names(new.people)


def follow_faces(app: SearchApp, runtime: Runtime) -> None:
    """Give the library the faces named since it was built.

    Args:
        app: The library.
        runtime: The runtime now.
    """
    people = runtime.settings.people
    search, index = app.place.index, runtime.index_file
    if isinstance(search, MeaningIndex) and index is not None:
        search.name_people_soon(NamesKept(index, people))
    desk = app.place.names
    desk.place = replace(desk.place, settings=people)
    desk.seen = None  # read again at its next cross


def _names(people: PeopleSettings) -> tuple[str, ...]:
    """The names of the people, in order.

    Args:
        people: `[people]`.

    Returns:
        Their names.
    """
    return tuple(person.name for person in people.person)
