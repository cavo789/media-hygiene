"""`POST /api/place`: my places with their counts, and *📍 Place…* on the picked (0553).

The photos go into `places/<name>.toml` (`give_photos`), the file is read back, and the
answer counts what it holds. A photo already in the place by its GPS is not written,
and said. A photo given another place leaves it: a photo has one place.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.config.place_photos import HandPhoto, PlacePhotos
from media_hygiene.i18n import _, ngettext
from media_hygiene.places.config_photos import give_photos, read_place_photos
from media_hygiene.review.config_saving import save_refused
from media_hygiene.review.serving import json_response
from media_hygiene.search.aside_filter import AsideFilter
from media_hygiene.search.place_neighbours import neighbours
from media_hygiene.search.tag_desk import ref_of

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.review.http import Response
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.search.place_book import PlaceBook, PlaceMembers
    from media_hygiene.search.query import SearchQuery

PLACE_PATH: Final = "/api/place"
_MOST: Final = 20_000  # photos picked at once, as *Move to an event…*


class PlaceAsked(BaseModel):
    """What the page asks: the places, or some photos given one."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Literal["list", "give"] = "list"
    keys: tuple[int, ...] = Field(default=(), max_length=_MOST)
    place: str = Field(default="", max_length=200)


@dataclass(frozen=True, slots=True)
class PlaceDesk:
    """My places on the search page."""

    index: SearchIndex
    mapper: HostPathMapper
    book: PlaceBook
    writable: bool  # `/config` can be written
    aside: Callable[[], frozenset[str]]

    def narrow(self, query: SearchQuery, place: str, *, unplaced: bool) -> SearchQuery:
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

    def answer(self, body: bytes) -> Response:
        """List my places, or give one to the photos picked.

        Args:
            body: `PlaceAsked`, as JSON.

        Returns:
            Every place and its count, read back, and the line said; 400 for a body
            that cannot be read, 409 without a writable `/config`, 422 or 500 when
            the save fails.
        """
        try:
            asked = PlaceAsked.model_validate_json(body)
        except ValidationError as exc:
            said = exc.errors()[0]["msg"] if exc.errors() else str(exc)
            return json_response(HTTPStatus.BAD_REQUEST, {"error": said})
        try:
            said, near = "", list[int]()
            if asked.action == "give":
                if not self.writable:
                    message = _(
                        "Places cannot be saved: /config is not mounted, or read-only."
                    )
                    return json_response(HTTPStatus.CONFLICT, {"error": message})
                said, near = self._give(asked)
            members = self.book.members()
        except (ValueError, OSError) as exc:
            return save_refused(exc)
        rows = [{"name": n, "count": len(members.of(n))} for n in members.names]
        return json_response(
            HTTPStatus.OK, {"places": rows, "saved": said, "near": near}
        )

    def _give(self, asked: PlaceAsked) -> tuple[str, list[int]]:
        """Write the photos not in the place yet, then count them in the file.

        Args:
            asked: The keys and the place.

        Returns:
            The line to say, and the keys of the photos it may suit too (0554).

        Raises:
            ValueError: No such place, or no photo picked.
        """
        members = self.book.members()
        wanted = asked.place.casefold()
        name = next((n for n in members.names if n.casefold() == wanted), None)
        if name is None or not asked.keys:
            raise ValueError(_("Choose one of your places, pick a photo."))
        found = {
            k: photo.path for k in asked.keys if (photo := self.index.source_of(k))
        }
        kept = set(AsideFilter(self.aside, self.mapper).keep(found.values()).files)
        keys = [key for key, path in found.items() if path in kept]
        by_gps = [key for key in keys if _by_gps(members, wanted, found[key])]
        refs = (
            ref_of(self.index, self.mapper, key) for key in keys if key not in by_gps
        )
        photos = tuple(HandPhoto(path=r.path, id=r.id) for r in refs if r is not None)
        if photos:
            give_photos(self.book.config_file, PlacePhotos(place=name, photos=photos))
        held = {
            photo.id
            for entry in read_place_photos(self.book.config_file)
            if entry.place.casefold() == wanted
            for photo in entry.photos
        }
        count = sum(1 for photo in photos if photo.id in held)
        said = ngettext(
            "{n} photo saved in {place}, read back from the disk.",
            "{n} photos saved in {place}, read back from the disk.",
            count,
        ).format(n=count, place=name)
        if by_gps:
            said += " " + ngettext(
                "{n} already there by its GPS: not written.",
                "{n} already there by their GPS: not written.",
                len(by_gps),
            ).format(n=len(by_gps))
        return said, self._near([found[key] for key in keys])

    def _near(self, given: list[Path]) -> list[int]:
        """The keys of the photos a place given may suit too (0554).

        Args:
            given: The photos given.

        Returns:
            Those of the same day and folder, without a place, not set aside.
        """
        placed = self.book.members().placed()
        near = neighbours(self.index.connection, given, placed)
        shown = AsideFilter(self.aside, self.mapper).keep(near).files
        return [near[path] for path in shown]


def _by_gps(members: PlaceMembers, name: str, path: Path) -> bool:
    """Tell whether a photo lies in a place by its position.

    Args:
        members: The members.
        name: The folded place.
        path: The photo.

    Returns:
        True when its circle or area holds it.
    """
    return path in members.by_gps.get(name, frozenset())
