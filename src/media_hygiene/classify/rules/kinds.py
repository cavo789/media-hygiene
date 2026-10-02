"""What a rule matches on, and the kinds of files told from their metadata alone."""

from __future__ import annotations

from enum import StrEnum
from typing import Final

from media_hygiene.classify.models import SortReason


class RuleMatch(StrEnum):
    """The `match` of a rule: which facts of a file it reads."""

    EXISTING_FOLDER = "existing_folder"
    EVENT_NEIGHBOUR = "event_neighbour"
    CALENDAR = "calendar"
    DATE_RANGE = "date_range"
    PLACE = "place"
    TRIP = "trip"
    KIND = "kind"
    PATH = "path"
    CAMERA = "camera"
    SUBJECT = "subject"
    OTHER_CATEGORY = "other_category"


class FileKind(StrEnum):
    """Files that are not ordinary shots, told from their name and metadata."""

    SCREENSHOT = "screenshot"  # screenshots, documents, tiny images
    RECEIVED = "received"  # received through a messaging app, no EXIF
    DOWNLOAD = "download"  # downloaded films and series: not memories


# The rules whose category comes from the folders, not from the rule.
BUILT_IN: Final = frozenset({RuleMatch.EXISTING_FOLDER, RuleMatch.EVENT_NEIGHBOUR})
DATED: Final = frozenset({RuleMatch.CALENDAR, RuleMatch.DATE_RANGE})
# The rules read from the GPS: their category without one, and the reason of the
# files without GPS that inherit them from their event.
GEO_CATEGORIES: Final = {RuleMatch.PLACE: "{place}", RuleMatch.TRIP: "{country}/{city}"}
NEIGHBOURS: Final = {
    RuleMatch.PLACE: SortReason.PLACE_NEIGHBOUR,
    RuleMatch.TRIP: SortReason.TRIP_NEIGHBOUR,
}
REASONS: Final = {
    RuleMatch.EVENT_NEIGHBOUR: SortReason.EVENT_NEIGHBOUR,
    RuleMatch.CALENDAR: SortReason.CALENDAR,
    RuleMatch.DATE_RANGE: SortReason.DATE_RANGE,
    RuleMatch.KIND: SortReason.KIND,
    RuleMatch.PATH: SortReason.PATH,
    RuleMatch.CAMERA: SortReason.CAMERA,
    RuleMatch.SUBJECT: SortReason.SUBJECT,
    RuleMatch.PLACE: SortReason.PLACE,
    RuleMatch.TRIP: SortReason.TRIP,
    RuleMatch.OTHER_CATEGORY: SortReason.OTHER_CATEGORY,
}
