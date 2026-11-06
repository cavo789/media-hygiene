"""Narrows a search as the page's list was, for *Pick all N found* (0602, 0642).

The "all" re-runs of `/api/chosen` and `/api/albums` go through here: the album filter
and the Place filter, read again at each request, so they reach the files shown, never
those a filter hides.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from media_hygiene.search.album_filter import AlbumNarrow
    from media_hygiene.search.place_book import PlaceBook
    from media_hygiene.search.query import SearchQuery
    from media_hygiene.search.views import SearchAsked


@dataclass(frozen=True, slots=True)
class PlaceNarrow:
    """Narrows a search to the Place filter, members read through the book."""

    book: PlaceBook

    def query(self, query: SearchQuery, place: str, *, unplaced: bool) -> SearchQuery:
        """Keep a search to a place's photos, or to the photos without a place.

        Args:
            query: The search.
            place: One of my places; empty: any.
            unplaced: Only the photos without a place.

        Returns:
            The search, narrowed; as it is when the settings cannot be read.
        """
        if not place and not unplaced:
            return query
        try:
            members = self.book.members()
        except ValueError:
            return query
        filters = query.filters
        if unplaced:
            out = {str(path) for path in members.placed()} | set(filters.without)
            filters = replace(filters, without=tuple(sorted(out)))
        if place:
            inside = {str(path) for path in members.of(place)}
            if filters.only is not None:
                inside &= set(filters.only)
            filters = replace(filters, only=tuple(sorted(inside)))
        return replace(query, filters=filters)


@dataclass(frozen=True, slots=True)
class FoundNarrow:
    """The filters of the page that the search's own words do not hold."""

    albums: AlbumNarrow
    places: PlaceNarrow

    def query(self, query: SearchQuery, asked: SearchAsked) -> SearchQuery:
        """Keep a search to what the page's filters show.

        Args:
            query: The search.
            asked: What the page sent: its album filter, its place, what is missing.

        Returns:
            The search, narrowed as `POST /api/search` narrows it.
        """
        kept = self.albums.query(query, asked.album)
        unplaced = asked.missing == "place"
        return self.places.query(kept, asked.place, unplaced=unplaced)
