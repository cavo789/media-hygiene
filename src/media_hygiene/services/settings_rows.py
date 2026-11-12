"""The settings the pages change, one row each, and where each one is (0670).

Every group of `review/setting_groups.py` has its row (a test checks it), then the
other values a page writes into `config.toml` (the disk space, the scan scope, the
strictness of the reviews…). A row only says where the setting is: it is changed on
its own page, never here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from media_hygiene.i18n import _
from media_hygiene.review.album_show import SLIDESHOW_PAGE
from media_hygiene.review.setting_groups import EVENTS_PATH, LOCALE_PATH, SLIDESHOW_PATH
from media_hygiene.review.step_watch import DISK_PAGE
from media_hygiene.search.app import SEARCH_PAGE_PATH
from media_hygiene.search.events_desk import EVENTS_PAGE_PATH
from media_hygiene.search.folder_role_desk import ROLES
from media_hygiene.services.burst_opening import BURST_KEYS, BURST_SECTION
from media_hygiene.services.unwanted_reviewing import UNWANTED_KEYS, UNWANTED_SECTION

# The anchor of the events page's *Group the photos…* (`search_events_grouping`).
GROUPING_ANCHOR: Final = "#grouping"
_LOCALE_ANCHOR: Final = "#mhLocale"  # the picker of every page's bar, this one's too


@dataclass(frozen=True, slots=True)
class SettingRow:
    """One setting as the index lists it."""

    title: str
    what: str  # one line: what it does
    href: str  # its page, the setting unfolded when the page can
    keys: tuple[
        str, ...
    ]  # its keys in `config.toml`, dotted (`classify.min_event_size`)
    group: str = ""  # the route of its group in `setting_groups`, when it has one


def _dotted(section: tuple[str, ...], keys: tuple[str, ...]) -> tuple[str, ...]:
    """The keys of a table, dotted."""
    return tuple(".".join((*section, key)) for key in keys)


def _grouped() -> tuple[SettingRow, ...]:
    """The rows of the groups of `setting_groups`."""
    events = ("merge_gap_hours", "min_event_size", "trip_min_km")
    return (
        SettingRow(
            _("Language"),
            _("The language of the pages and of the console's messages."),
            _LOCALE_ANCHOR,
            ("general.locale",),
            LOCALE_PATH,
        ),
        SettingRow(
            _("Slideshow pace"),
            _("Seconds each photo stays on the TV: on the remote, once a show starts."),
            SLIDESHOW_PAGE,
            ("slideshow.interval_seconds",),
            SLIDESHOW_PATH,
        ),
        SettingRow(
            _("Events grouping"),
            _("How the photos are grouped into events and trips."),
            f"{EVENTS_PAGE_PATH}{GROUPING_ANCHOR}",
            _dotted(("classify",), events),
            EVENTS_PATH,
        ),
    )


def _elsewhere() -> tuple[SettingRow, ...]:
    """The other values a page writes into `config.toml`."""
    return (
        SettingRow(
            _("Local AI"),
            _("The local vision model that describes the photos; none: off."),
            "/#settings/aiCard",
            ("classify.ai.model", "classify.ai.url"),
        ),
        SettingRow(
            _("Disk space"),
            _("How large the previews may grow, when to suggest a purge."),
            DISK_PAGE,
            ("cache.previews_max_gb", "clean.purge_hint_days"),
        ),
        SettingRow(
            _("What the audit analyses"),
            _("The kinds of files analysed and the folder names ignored."),
            "/#clean/auditHere",
            ("scan.extensions", "scan.excluded_names"),
        ),
        SettingRow(
            _("Phones on the network"),
            _("Whether a phone may open the pages, and see the originals."),
            "/#share/lanSwitch",
            ("review.lan", "review.lan_phone_originals"),
        ),
        SettingRow(
            _("After an import"),
            _("The steps run once the photos of a phone are copied."),
            "/#import/importSteps",
            ("imports.then",),
        ),
        SettingRow(
            _("Home page"),
            _("The actions starred and the order of the tiles."),
            "/#home/tilesCard",
            ("home.favorites", "home.tiles"),
        ),
        SettingRow(
            _("Folder roles"),
            _("The folders protected, preferred, backups or not analysed."),
            SEARCH_PAGE_PATH,
            _dotted(("folders",), ROLES),
        ),
        SettingRow(
            _("Albums folder"),
            _("Where the albums are made."),
            "/albums",
            ("album.root",),
        ),
        SettingRow(
            _("Sorting"),
            _("Where sort moves the photos, and the folders it makes."),
            SEARCH_PAGE_PATH,
            _dotted(("classify",), ("target", "layout", *_LAYOUTS)),
        ),
        SettingRow(
            _("Burst series strictness"),
            _("When a shot of a series is offered to set aside."),
            "/#clean",
            _dotted(BURST_SECTION, BURST_KEYS),
        ),
        SettingRow(
            _("Junk strictness"),
            _("What the junk review counts as a screenshot, too small, too dark…"),
            "/#clean",
            _dotted(UNWANTED_SECTION, UNWANTED_KEYS),
        ),
        SettingRow(
            _("Places"),
            _("Your places, the spots ignored, naming places online."),
            "/places/",
            (
                "classify.places",
                "classify.place_photos",
                "places.ignored",
                "places.reverse_lookup",
            ),
        ),
        SettingRow(
            _("Event rules"),
            _("The rules that name the events and choose their folders."),
            EVENTS_PAGE_PATH,
            ("classify.rules",),
        ),
        SettingRow(
            _("Tags"),
            _("The synonyms and the words never used as a tag."),
            SEARCH_PAGE_PATH,
            ("tags.synonyms", "tags.stop_words"),
        ),
    )


_LAYOUTS: Final = (
    "unsure_layout",
    "manual_layout",
    "undated_layout",
    "received_layout",
)


def setting_rows() -> tuple[SettingRow, ...]:
    """Every row, in the language in use: the groups first.

    Returns:
        Them.
    """
    return (*_grouped(), *_elsewhere())
