"""The desks of *📅 Date…*, *📍 Place…* and the files set aside, from the runtime."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.search.chosen_api import ChosenDesk
from media_hygiene.search.date_desk import DateDesk
from media_hygiene.search.found_narrow import FoundNarrow, PlaceNarrow
from media_hygiene.search.hand_index import HandIndex
from media_hygiene.search.place_book import PlaceBook
from media_hygiene.search.place_desk import PlaceDesk
from media_hygiene.services.albums import album_narrow
from media_hygiene.services.chosen_place import chosen_store, reports_ready
from media_hygiene.services.date_sidecars import DateWriter
from media_hygiene.services.names_file import names_file
from media_hygiene.services.xmp_towns import indexed_inputs

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.geo.distance import Point
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.runtime import Runtime


def date_desk(
    runtime: Runtime, search: SearchIndex, chosen: ChosenDesk
) -> DateDesk | None:
    """*📅 Date…*: the sidecars' days read now, for the search.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.
        chosen: The files set aside, left out.

    Returns:
        The desk; None on a search that cannot hold the days (a test's index).
    """
    if not isinstance(search, HandIndex):
        return None
    desk = DateDesk(search, runtime.mapper, DateWriter(runtime), chosen.paths)
    desk.read_again()
    return desk


def _points(runtime: Runtime, search: SearchIndex) -> Mapping[Path, Point]:
    """Where each located file was taken: its GPS, or its Takeout `.json`'s.

    Args:
        runtime: Mount points.
        search: The open index.

    Returns:
        The positions.
    """
    return indexed_inputs(runtime, search.connection).points


def place_book(runtime: Runtime, search: SearchIndex) -> PlaceBook:
    """Who is in which of my places, read when first asked.

    Args:
        runtime: Settings and mount points.
        search: The open index.

    Returns:
        The book.
    """
    return PlaceBook(
        search.connection,
        runtime.locations.config_file,
        partial(_points, runtime, search),
    )


def place_desk(runtime: Runtime, search: SearchIndex, chosen: ChosenDesk) -> PlaceDesk:
    """The Place filter and *📍 Place…*.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.
        chosen: The files set aside, left out.

    Returns:
        The desk.
    """
    writable = names_file(runtime) is not None
    book = chosen.narrowing.places.book  # one book: its members are costly to read
    return PlaceDesk(search, runtime.mapper, book, writable, chosen.paths)


def chosen_desk(runtime: Runtime, search: SearchIndex) -> ChosenDesk:
    """The files set aside from the pages: `decisions.json` in the reports folder.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.

    Returns:
        The desk answering the pages about them; its "all" follows the album and
        place filters.
    """
    ready = partial(reports_ready, runtime)
    places = PlaceNarrow(place_book(runtime, search))
    narrowing = FoundNarrow(album_narrow(runtime), places)
    return ChosenDesk(chosen_store(runtime), search, ready, narrowing)
