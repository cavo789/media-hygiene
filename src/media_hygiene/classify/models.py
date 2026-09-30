"""The vocabulary of `classify`: dated files, events, and one proposal per file."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from media_hygiene.classify.layout import Values
    from media_hygiene.scan.metadata import MediaMetadata
    from media_hygiene.scan.models import VisualFacts


class DateSource(StrEnum):
    """Where the date of a file comes from, the most reliable first."""

    EXIF = "exif"
    VIDEO = "video"
    NAME = "name"
    FOLDER = "folder"
    MTIME = "mtime"


class SortReason(StrEnum):
    """Why a file goes where it is proposed to go (like `KeepReason` for `clean`)."""

    EXISTING_FOLDER = "existing-folder"
    PERSON_FOLDER = "person-folder"
    EVENT_NEIGHBOUR = "event-neighbour"
    DATE_ONLY = "date-only"
    NO_SIGNAL = "no-signal"
    UNDATED = "undated"
    LEFT_AS_IS = "left-as-is"


class Band(StrEnum):
    """How sure the proposal is, which decides its layout."""

    SURE = "sure"
    UNSURE = "to-check"
    MANUAL = "manual"
    UNDATED = "undated"
    STAY = "stay"


@dataclass(frozen=True, slots=True)
class MediaInput:
    """One media file and what the index knows of it."""

    path: Path
    root: Path
    size: int
    mtime_ns: int
    visual: VisualFacts | None = None
    metadata: MediaMetadata | None = None
    digest: str | None = None

    @property
    def taken_at(self) -> str | None:
        """The EXIF date, as written.

        Returns:
            It, or None.
        """
        return self.visual.taken_at if self.visual else None

    @property
    def camera(self) -> str | None:
        """The EXIF make and model.

        Returns:
            Them, or None.
        """
        return self.visual.camera if self.visual else None


@dataclass(frozen=True, slots=True)
class Dating:
    """The date of a file, where it comes from, and how much it is trusted (0-100)."""

    when: datetime
    source: DateSource
    confidence: int


@dataclass(frozen=True, slots=True)
class Event:
    """Files taken close together: the unit a user names once."""

    event_id: str
    start: datetime
    end: datetime
    paths: tuple[Path, ...]
    label: str = ""

    @property
    def span(self) -> str:
        """The event's default name: `2016-07-01..07-15`, or one day.

        Returns:
            Its dates, folder-safe.
        """
        first, last = self.start.date(), self.end.date()
        if first == last:
            return first.isoformat()
        tail = last.isoformat() if first.year != last.year else last.isoformat()[5:]
        return f"{first.isoformat()}..{tail}"


@dataclass(frozen=True, slots=True)
class Verdict:
    """How sure a proposal is: its band, its reason and its score (0-100)."""

    band: Band
    reason: SortReason
    score: int


@dataclass(frozen=True, slots=True)
class Proposal:
    """Where one file should go, and why."""

    file: MediaInput
    dating: Dating | None
    verdict: Verdict
    values: Values | None = None  # what the layout was rendered from; None: stays
    event_id: str = ""
    folder: str | None = None  # relative to the target root; None: stay where it is
    target: Path | None = None  # the target folder, absolute (container path)

    @property
    def band(self) -> Band:
        """The band of the proposal.

        Returns:
            It.
        """
        return self.verdict.band

    @property
    def category(self) -> str:
        """The category proposed.

        Returns:
            It, or an empty string.
        """
        return self.values.category if self.values else ""

    @property
    def reason(self) -> SortReason:
        """Why the file goes there.

        Returns:
            The reason.
        """
        return self.verdict.reason

    @property
    def in_place(self) -> bool:
        """Tell whether the file is already where it should be.

        Returns:
            True when it stays, or its folder is the proposed one.
        """
        return self.target is None or self.target == self.file.path.parent
