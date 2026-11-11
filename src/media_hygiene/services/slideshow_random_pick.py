"""The photos of a random show, read from the index (0508): what `journey` walks.

Photos only (no video), dated (an undated photo cannot be placed in time), under the
folders analysed, neither set aside nor a screenshot or a document (`classify`'s
`is_screenshot`, on what the index knows of the file), and taken by a camera: a make,
a model or a position in its EXIF (`has_camera_trace`), so that a picture received or
saved from an app without them is left out too. Read-only.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.classify.dates import exif_datetime
from media_hygiene.classify.dating import has_camera_trace
from media_hygiene.classify.events import EventRules
from media_hygiene.classify.models import MediaInput
from media_hygiene.classify.rules.matchers import is_screenshot
from media_hygiene.report.thumbnails import PREVIEWABLE
from media_hygiene.scan.filters import media_kind
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.services.aside_paths import set_aside
from media_hygiene.services.slideshow_pick import MAX_SLIDES
from media_hygiene.services.slideshow_random import Journey, journey

if TYPE_CHECKING:
    from datetime import datetime

    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.runtime import Runtime

_ROWS: Final = (
    "SELECT path, size, mtime_ns, media_date, metadata FROM files"
    " WHERE media_date IS NOT NULL"
)
_SECONDS_PER_MINUTE: Final = 60
_SHORTEST, _LONGEST = 30, 120  # minutes the phone offers: 30, 60 or 120
_FIRST_YEAR, _LAST_YEAR = 1800, 2200


class RandomAsk(BaseModel):
    """What the phone asks for a random show: its length, and the years."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    minutes: int = Field(default=60, ge=_SHORTEST, le=_LONGEST)
    first_year: int | None = Field(default=None, ge=_FIRST_YEAR, le=_LAST_YEAR)
    last_year: int | None = Field(default=None, ge=_FIRST_YEAR, le=_LAST_YEAR)


def random_files(
    runtime: Runtime, search: SearchIndex, ask: RandomAsk
) -> tuple[Path, ...]:
    """The files of a random show, in its order; a new seed each time.

    Args:
        runtime: Settings, mount points and the host mapper.
        search: The open index.
        ask: The length and the years.

    Returns:
        The photos, at most `MAX_SLIDES`; none when the index has no dated photo.
    """
    settings = runtime.settings
    slides = ask.minutes * _SECONDS_PER_MINUTE // settings.slideshow.interval_seconds
    years = None
    if ask.first_year is not None or ask.last_year is not None:
        first = ask.first_year or _FIRST_YEAR
        years = (first, max(first, ask.last_year or _LAST_YEAR))
    rules = EventRules.of(
        settings.classify.session_gap_hours, settings.classify.merge_gap_hours, 1
    )
    asked = Journey(min(slides, MAX_SLIDES), rules, years, time.time_ns())
    return tuple(journey(dated_photos(runtime, search), asked))


def dated_photos(runtime: Runtime, search: SearchIndex) -> list[tuple[Path, datetime]]:
    """The photos a random show may take, with their dates.

    Args:
        runtime: Settings, mount points and the host mapper.
        search: The open index.

    Returns:
        Each photo and its date.
    """
    data = runtime.locations.data_dir
    aside = set_aside(runtime)
    found: list[tuple[Path, datetime]] = []
    for text, size, mtime, written, facts in search.connection.execute(_ROWS):
        path = Path(text)
        when = exif_datetime(written)
        if when is None or media_kind(path) not in PREVIEWABLE:
            continue
        if not path.is_relative_to(data) or runtime.mapper.to_host(path) in aside:
            continue
        known = MediaInput(path, path.parent, size, mtime or 0, metadata=_facts(facts))
        if has_camera_trace(known) and not is_screenshot(known):
            found.append((path, when))
    return found


def _facts(text: object) -> MediaMetadata | None:
    """The metadata the index keeps, when it reads.

    Args:
        text: The JSON column.

    Returns:
        The metadata, or None.
    """
    if not isinstance(text, str):
        return None
    try:
        return MediaMetadata.model_validate_json(text)
    except ValidationError:
        return None
