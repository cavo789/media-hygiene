"""`media-hygiene search`: find photos by their words, in the console or the browser.

The index (`/cache`) is read, never written: the full-text table lives in memory. The
browser page is served like `review`, until Ctrl+C; the grid's previews are kept in
the cache folder. Nothing in the photo folders is ever changed.
"""

from __future__ import annotations

import asyncio
import contextlib
import sqlite3
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.console.search_view import show_found
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.search.app import SEARCH_PATH, SearchApp, SearchPlace
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.people_words import people_words, unknown_people
from media_hygiene.search.query import SearchQuery, parse_terms
from media_hygiene.search.thumbs import PREVIEWS_DIR_NAME
from media_hygiene.services.data_checks import unreadable_index
from media_hygiene.services.reviewing import address_tip, page_url, run_server

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

_PACKAGE: Final = "media_hygiene.search"
_PAGE_TEMPLATE: Final = "search.html.j2"


@dataclass(frozen=True, slots=True)
class Printed:
    """`search "words"`: the words, and how many files to print at most."""

    text: str
    limit: int


def open_search(runtime: Runtime) -> SearchIndex:
    """Open the index read-only; say when no file has words yet.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The search, to close after use.

    Raises:
        MountError: The cache is not mounted, holds no index, or cannot be read.
    """
    index = runtime.index_file
    if index is None or not index.is_file():
        cache = runtime.mapper.to_host(runtime.locations.cache_dir)
        raise MountError(
            _("No index in {folder}: nothing to search yet.").format(folder=cache),
            _(
                "Run 'audit', then 'tags', with the same /cache mount: search "
                "finds the words they keep there."
            ),
        )
    try:
        search = SearchIndex.open(index)
        search.name_people(people_words(search.connection, runtime.settings.people))
        empty = search.find(SearchQuery(()), 1).total == 0
    except sqlite3.Error as exc:
        raise unreadable_index(runtime, index, exc) from exc
    if empty:
        runtime.output.warning(_("No file has words yet: nothing can be found."))
        runtime.output.tip(
            _(
                "Run 'tags' first: it gives every photo the words of its folders, "
                "date and place."
            )
        )
    return search


def print_found(runtime: Runtime, search: SearchIndex, printed: Printed) -> int:
    """Print the first files matching the words, best first.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.
        printed: The words and the limit.

    Returns:
        How many files match.
    """
    query = SearchQuery(parse_terms(printed.text))
    unknown = unknown_people(query, runtime.settings.people)
    if unknown is not None:
        runtime.output.warning(unknown)
    found = search.find(query, printed.limit)
    show_found(runtime.output, found, runtime.mapper)
    return found.total


def serve_search(runtime: Runtime, search: SearchIndex, port: int) -> None:
    """Serve the search page until Ctrl+C.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.
        port: The port to listen on, inside the container (0: any free one).
    """
    environment = translated_environment(_PACKAGE, escaped=("html", "j2"))
    page = environment.get_template(_PAGE_TEMPLATE).render(search_path=SEARCH_PATH)
    previews = runtime.locations.cache_dir / PREVIEWS_DIR_NAME
    place = SearchPlace(search, runtime.mapper, previews, runtime.settings.people)
    with runtime.executor_factory() as executor, contextlib.suppress(KeyboardInterrupt):
        app = SearchApp(place, page.encode(), executor)
        asyncio.run(run_server(app, port, partial(_announce, runtime)))


def _announce(runtime: Runtime, port: int) -> None:
    """Tell where the page is and how to open it from the host.

    Args:
        runtime: Settings, mount points and output.
        port: The port listened on, inside the container.
    """
    runtime.output.success(
        _(
            "Search ready, open {url} in your browser. Ctrl+C stops it; nothing is "
            "changed."
        ).format(url=page_url(port))
    )
    address_tip(runtime.output, port)
