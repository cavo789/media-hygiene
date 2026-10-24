"""`search` and `browse`: find photos by their words, or walk through the folders.

The index (`/cache`) is read, never written: the full-text table lives in memory. The
browser page is served like `review`, until Ctrl+C; the grid's previews are kept in
the cache folder. Nothing in the photo folders is ever changed: the files set aside on
the page are written into the decisions file (`/reports`), for `clean --decisions`.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.console.search_view import show_found
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.search.app import SEARCH_PAGE_PATH
from media_hygiene.search.folders import BROWSE_PATH
from media_hygiene.search.meaning_index import MeaningIndex
from media_hygiene.search.names_soon import names_soon
from media_hygiene.search.people_words import unknown_people
from media_hygiene.search.query import SearchQuery, parse_terms
from media_hygiene.services.data_checks import unreadable_index
from media_hygiene.services.search_meaning import with_meaning
from media_hygiene.services.search_pages import PageStart, Served, serve_pages

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.apply_api import ApplyStep
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class Printed:
    """`search "words"`: the words, and how many files to print at most."""

    text: str
    limit: int


def open_search(runtime: Runtime, *, words: bool = True) -> SearchIndex:
    """Open the index read-only; say when no file has words yet.

    Args:
        runtime: Settings, mount points and output.
        words: Whether the words matter (`search`); the folder view needs none.

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
        search = MeaningIndex.open(index)
        # Read meanwhile (0354): the page answers without waiting for them.
        search.name_people_soon(names_soon(index, runtime.settings.people))
        # A file with a tag is a file with words: no need to wait for the names then.
        empty = (
            words and not search.tagged and search.find(SearchQuery(()), 1).total == 0
        )
        with_meaning(runtime, search)
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


def serve_search(runtime: Runtime, search: SearchIndex, port: int) -> int:
    """Serve the search page until Ctrl+C.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.
        port: The port to listen on, inside the container (0: any free one).

    Returns:
        How many files are set aside when the page stops, read from the disk.
    """
    ready = _(
        "Search ready, open {url} in your browser. Ctrl+C stops it; your photos "
        "are not changed."
    )
    start = PageStart(port, SEARCH_PAGE_PATH, ready)
    return serve_pages(runtime, search, start).chosen


@dataclass(frozen=True, slots=True)
class BrowseStart:
    """`browse`: its port, and the step *Apply now* ends on (opened from home)."""

    port: int  # inside the container (0: any free one)
    apply: Callable[[], ApplyStep | None] | None = None  # None: no button


def serve_browse(runtime: Runtime, search: SearchIndex, start: BrowseStart) -> Served:
    """Serve the folder view until Ctrl+C, or *Apply now*.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.
        start: The port, and the step *Apply now* ends on.

    Returns:
        How many files are set aside when the page stops, read from the disk, and
        `STEP_EXIT_BASE + n` when *Apply now* chose step `n`.
    """
    ready = _(
        "Your folders are ready, open {url} in your browser. Ctrl+C stops it; your "
        "photos are not changed."
    )
    return serve_pages(
        runtime, search, PageStart(start.port, BROWSE_PATH, ready, start.apply)
    )
