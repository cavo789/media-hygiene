"""What the search page sends and receives, in JSON."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.search.query import Filters, SearchQuery, parse_terms
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
# The sentence is shown under the picture; the words of the others as chips.
_SHOWN: Final = tuple(source for source in TagSource if source is not TagSource.CAPTION)


class SearchAsked(BaseModel):
    """`POST /api/search`: the words typed, and the filters of the page."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str = Field(default="", max_length=_MAX_TEXT)
    year_from: int | None = Field(default=None, ge=_FIRST_YEAR, le=_LAST_YEAR)
    year_to: int | None = Field(default=None, ge=_FIRST_YEAR, le=_LAST_YEAR)
    folder: str = Field(default="", max_length=_MAX_TEXT)
    source: TagSource | None = None

    def query(self) -> SearchQuery:
        """Make the search of what the page sent.

        Returns:
            The query; one year alone is a range of one year, reversed years are
            put back in order.
        """
        bounds = [year for year in (self.year_from, self.year_to) if year is not None]
        years = (min(bounds), max(bounds)) if bounds else None
        filters = Filters(years, self.folder, self.source)
        return SearchQuery(parse_terms(self.text), filters)


def found_view(found: Found, mapper: HostPathMapper) -> dict[str, object]:
    """Write what a search found for the page.

    Args:
        found: The total and the first files.
        mapper: Writes the paths as the user knows them (host paths).

    Returns:
        The JSON object.
    """
    return {
        "total": found.total,
        "hits": [_hit_view(hit, mapper) for hit in found.hits],
    }


def _hit_view(hit: Hit, mapper: HostPathMapper) -> dict[str, object]:
    """Write one file found for the page.

    Args:
        hit: The file.
        mapper: Writes its path as the user knows it.

    Returns:
        The JSON object: name, folder, date, sentence, words, and its addresses.
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
    }
