"""What the search page sends and receives, in JSON."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.search.query import Filters, SearchQuery, Sorting, parse_terms
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.search.models import Found, Hit

THUMB_PREFIX: Final = "/thumb/"
PREVIEW_PREFIX: Final = "/preview/"
ORIGINAL_PREFIX: Final = "/original/"
JPEG: Final = ".jpg"
_MAX_TEXT: Final = 500
_FIRST_YEAR, _LAST_YEAR = 1800, 2200
_DECEMBER, _LAST_DAY = 12, 31
# The sentence is shown under the picture; the words of the others as chips.
_SHOWN: Final = tuple(source for source in TagSource if source is not TagSource.CAPTION)


class SearchAsked(BaseModel):
    """`POST /api/search`: the words typed, and the filters of the page."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str = Field(default="", max_length=_MAX_TEXT)
    year_from: int | None = Field(default=None, ge=_FIRST_YEAR, le=_LAST_YEAR)
    year_to: int | None = Field(default=None, ge=_FIRST_YEAR, le=_LAST_YEAR)
    day_from: date | None = None  # the calendars of the page (0396)
    day_to: date | None = None
    folder: str = Field(default="", max_length=_MAX_TEXT)
    source: TagSource | None = None
    sorting: Sorting = Sorting.ALL  # the sort convention's filter (0407)

    def query(self) -> SearchQuery:
        """Make the search of what the page sent.

        Returns:
            The query; one year or one day alone is a range of one, reversed bounds
            are put back in order.
        """
        filters = Filters(
            _range(self.year_from, self.year_to),
            self.folder,
            self.source,
            days=_range(self.day_from, self.day_to),
            sorting=self.sorting,
        )
        return SearchQuery(parse_terms(self.text), filters)

    def period(self) -> tuple[date, date] | None:
        """The days asked for: the calendars, else the years (1 January to 31 December).

        Returns:
            The first and last day; None without either.
        """
        days = _range(self.day_from, self.day_to)
        years = _range(self.year_from, self.year_to)
        if days is None and years is not None:
            days = (date(years[0], 1, 1), date(years[1], _DECEMBER, _LAST_DAY))
        return days

    def found_by(self) -> str:
        """Name the search in the decisions file, for the user's eyes.

        Returns:
            Its words and filters, e.g. `person:"Ann" · 2004-2006` or
            `2017-08-05..2017-08-06`; empty for none.
        """
        query = self.query()
        years, days = query.filters.years, query.filters.days
        parts = (
            str.strip(self.text),
            f"{years[0]}-{years[1]}" if years else "",
            _days_named(days) if days else "",
            str.strip(self.folder),
            query.filters.source.value if query.filters.source else "",
            "" if self.sorting is Sorting.ALL else self.sorting.value,
        )
        return " · ".join(part for part in parts if part)


def _range[T: (int, date)](first: T | None, last: T | None) -> tuple[T, T] | None:
    """Two bounds put in order; one alone is a range of one.

    Args:
        first: The first bound typed, if any.
        last: The last bound typed, if any.

    Returns:
        The range; None without either.
    """
    bounds = [bound for bound in (first, last) if bound is not None]
    return (min(bounds), max(bounds)) if bounds else None


def _days_named(days: tuple[date, date]) -> str:
    """Write a period as a `date_range` rule does.

    Args:
        days: The first and last day.

    Returns:
        `2017-08-05..2017-08-06`, or `2017-08-05` for one day.
    """
    first, last = (day.isoformat() for day in days)
    return first if first == last else f"{first}..{last}"


def found_view(
    found: Found, mapper: HostPathMapper, chosen: frozenset[str] = frozenset()
) -> dict[str, object]:
    """Write what a search found for the page.

    Args:
        found: The total and the first files.
        mapper: Writes the paths as the user knows them (host paths).
        chosen: The host paths of the files set aside.

    Returns:
        The JSON object.
    """
    hits = [_hit_view(hit, mapper) for hit in found.hits]
    for hit in hits:
        hit["chosen"] = hit["path"] in chosen  # the path stays: `/person` (0351)
    return {"total": found.total, "hits": hits}


def _hit_view(hit: Hit, mapper: HostPathMapper) -> dict[str, object]:
    """Write one file found for the page.

    Args:
        hit: The file.
        mapper: Writes its path as the user knows it.

    Returns:
        The JSON object: name, folder, date, sentence, words, its addresses, and
        its host path (`path`, for `/person`).
    """
    path = hit.photo.path
    caption = hit.tags.get(TagSource.CAPTION, ())
    return {
        "key": hit.key,
        "name": path.name,
        "folder": mapper.to_host(path.parent),
        "date": hit.date,
        "caption": caption[0] if caption else "",
        "tags": {
            source.value: list(hit.tags[source])
            for source in _SHOWN
            if source in hit.tags
        },
        "thumb": f"{THUMB_PREFIX}{hit.key}{JPEG}",
        "preview": f"{PREVIEW_PREFIX}{hit.key}{JPEG}",
        "original": f"{ORIGINAL_PREFIX}{hit.key}{path.suffix.lower()}",
        "path": mapper.to_host(path),
    }
