"""The long defaults of `[classify]`: dates in file names, library folders, scores."""

from __future__ import annotations

from typing import Final

# Dates in file names: named groups y, m, d (and H, M, S when written).
NAME_DATES: Final = (
    (
        r"(?:IMG|VID|PXL|MVIMG)?[_-]?(?P<y>\d{4})(?P<m>\d{2})(?P<d>\d{2})[_-]"
        r"(?P<H>\d{2})(?P<M>\d{2})(?P<S>\d{2}).*"
    ),
    r"(?:IMG|VID|AUD)-(?P<y>\d{4})(?P<m>\d{2})(?P<d>\d{2})-WA\d+",
    r"(?:Screenshot|Capture)[ _-]*(?P<y>\d{4})-?(?P<m>\d{2})-?(?P<d>\d{2}).*",
    (
        r"(?P<y>\d{4})-(?P<m>\d{2})-(?P<d>\d{2})[ _]"
        r"(?P<H>\d{2})[h.](?P<M>\d{2})[._](?P<S>\d{2}).*"
    ),
)
# Folders that hold a library rather than name it: never a meaning.
LIBRARY_FOLDERS: Final = (
    r"(My |Mes )?(Photos|Pictures|Images|Videos|Vidéos|Mes images)",
    r"(Family|Famille|Photos de famille|Family photos)",
)
# The score of each reason (0 to 100), compared with `sure` and `unsure`.
SCORES: Final = {
    "existing-folder": 90,
    "person-folder": 85,
    "event-neighbour": 70,
    "calendar": 85,
    "date-range": 95,  # a trip the user wrote down: sure
    "kind": 85,
    "path": 90,
    "camera": 90,
    "other-category": 85,  # only when no rule above matched
    "subject": 85,  # the samples of an event agree; else "to check"
    "person": 85,  # someone named on enough photos of the event
    "place": 90,  # within a personal place
    "place-neighbour": 70,  # no GPS, in an event at a personal place
    "trip": 90,  # far from home
    "trip-neighbour": 70,  # no GPS, in a trip
    "folder-town": 60,  # a folder named after a town: to check
    "date-only": 90,
    "no-signal": 0,
}
