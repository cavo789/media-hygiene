"""The desks of *📅 Date…* (0531) and *📍 Place…* (0553), built from the runtime."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.search.date_desk import DateDesk
from media_hygiene.search.hand_index import HandIndex
from media_hygiene.search.place_book import PlaceBook
from media_hygiene.search.place_desk import PlaceDesk
from media_hygiene.services.date_sidecars import DateWriter
from media_hygiene.services.people_page import names_file
from media_hygiene.services.xmp_towns import indexed_inputs

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.geo.distance import Point
    from media_hygiene.search.chosen_api import ChosenDesk
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


def place_desk(runtime: Runtime, search: SearchIndex, chosen: ChosenDesk) -> PlaceDesk:
    """The Place filter and *📍 Place…*.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.
        chosen: The files set aside, left out.

    Returns:
        The desk.
    """
    book = PlaceBook(
        search.connection,
        runtime.locations.config_file,
        partial(_points, runtime, search),
    )
    writable = names_file(runtime) is not None
    return PlaceDesk(search, runtime.mapper, book, writable, chosen.paths)
