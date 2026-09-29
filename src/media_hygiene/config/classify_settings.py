"""`[classify]` — how `classify` proposes a tree; every value is an example."""

from __future__ import annotations

from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, field_validator

from media_hygiene.classify.layout import check_layout
from media_hygiene.config.patterns import valid_patterns

_FROZEN = ConfigDict(frozen=True, extra="forbid")
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
    "date-only": 90,
    "no-signal": 0,
}


class ClassifySettings(BaseModel):
    """`[classify]` — layouts per band, events, and the confidence thresholds.

    Layouts are relative to the target root; an empty layout leaves the files where they
    are. `target` empty sorts each mounted folder in place.
    """

    model_config = _FROZEN

    target: str = ""
    leave: tuple[str, ...] = ()
    timezone: str = ""
    layout: str = "{year}/{category}"
    unsure_layout: str = "{year}/To check/{category}"
    manual_layout: str = "{year}/To sort/{event}"
    undated_layout: str = "To sort/Undated"
    received_layout: str = "To sort/Received and downloaded"
    session_gap_hours: float = 6
    merge_gap_hours: float = 18
    min_event_size: int = 5
    event_year: Literal["start", "per_file"] = "start"
    sure: int = 80
    unsure: int = 50
    scores: dict[str, int] = SCORES
    name_dates: tuple[str, ...] = NAME_DATES
    generic_folders: tuple[str, ...] = LIBRARY_FOLDERS

    @field_validator(
        "layout", "unsure_layout", "manual_layout", "undated_layout", "received_layout"
    )
    @classmethod
    def _valid_layout(cls, layout: str) -> str:
        """Refuse a layout with an unknown placeholder or a forbidden name.

        Args:
            layout: A layout.

        Returns:
            It, unchanged.
        """
        check_layout(layout)
        return layout

    @field_validator("name_dates", "generic_folders")
    @classmethod
    def _valid_patterns(cls, patterns: tuple[str, ...]) -> tuple[str, ...]:
        """Reject patterns that are not valid regular expressions.

        Args:
            patterns: Configured patterns.

        Returns:
            The patterns, unchanged.
        """
        return valid_patterns(patterns)
