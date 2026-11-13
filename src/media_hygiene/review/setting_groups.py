"""The groups of values pages save into `config.toml`, by route (0606, 0607, 0609).

Bounds and defaults come from the settings classes: a value the page may save is one
the next run loads.
"""

from __future__ import annotations

from typing import Final

from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.config.settings import GeneralSettings
from media_hygiene.config.share_settings import (
    HIGHEST_QUALITY,
    LARGEST_SIDE,
    LOWEST_QUALITY,
    SMALLEST_SIDE,
    ShareSettings,
)
from media_hygiene.config.slideshow_settings import (
    INTERVAL_SECONDS,
    LONGEST_INTERVAL,
    SHORTEST_INTERVAL,
)
from media_hygiene.constants import Locale
from media_hygiene.i18n import _, install
from media_hygiene.review.setting_group import Field, Held, SettingGroup

LOCALE_PATH: Final = "/api/setting-locale"
SLIDESHOW_PATH: Final = "/api/setting-slideshow"
EVENTS_PATH: Final = "/api/setting-events"
SHARE_PATH: Final = "/api/setting-share"
_CLASSIFY: Final = ClassifySettings()
_MOST_HOURS: Final = 24 * 30
_MOST_EVENT_SIZE: Final = 10_000
_MOST_KM: Final = 20_000


def _speak(values: Held) -> str:
    """Switch the server to the language read back (0644), and say what follows it.

    Args:
        values: `locale`, as `config.toml` now holds it (checked).

    Returns:
        The line the page shows, in that language.
    """
    install(Locale(str(values["locale"])))
    return _(
        "Applied now: this page reloads in this language, the other open pages and "
        "the console's messages follow at their next load."
    )


LOCALE: Final = SettingGroup(
    LOCALE_PATH,
    ("general",),
    (Field("locale", GeneralSettings().locale.value, choices=tuple(Locale)),),
    _speak,
)
SLIDESHOW: Final = SettingGroup(
    SLIDESHOW_PATH,
    ("slideshow",),
    (Field("interval_seconds", INTERVAL_SECONDS, SHORTEST_INTERVAL, LONGEST_INTERVAL),),
)
EVENTS: Final = SettingGroup(
    EVENTS_PATH,
    ("classify",),
    (
        Field("merge_gap_hours", float(_CLASSIFY.merge_gap_hours), 0, _MOST_HOURS),
        Field("min_event_size", _CLASSIFY.min_event_size, 1, _MOST_EVENT_SIZE),
        Field("trip_min_km", float(_CLASSIFY.trip_min_km), 1, _MOST_KM),
    ),
)
_SHARE: Final = ShareSettings()
# The copies `share` makes (0747), from the album bar's *Prepare for sending*.
SHARE: Final = SettingGroup(
    SHARE_PATH,
    ("share",),
    (
        Field("long_side_px", _SHARE.long_side_px, SMALLEST_SIDE, LARGEST_SIDE),
        Field("quality", _SHARE.quality, LOWEST_QUALITY, HIGHEST_QUALITY),
        Field("keep_gps", _SHARE.keep_gps),
    ),
)
GROUPS: Final = {one.path: one for one in (LOCALE, SLIDESHOW, EVENTS, SHARE)}
