"""One line of the inventory: a file of the index, and what is derived from its facts.

Derived means computed now, never stored: the date as `classify` reads it, the group of
identical files, and the quality and exposure labels of `[inventory]`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.dates import exif_date, video_date
from media_hygiene.constants import MediaKind
from media_hygiene.scan.filters import media_kind

if TYPE_CHECKING:
    from collections.abc import Mapping
    from datetime import tzinfo

    from media_hygiene.config.inventory_settings import InventorySettings
    from media_hygiene.index.listing import IndexedFile, SharedDigest
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.scan.metadata import MediaMetadata
    from media_hygiene.scan.models import VisualFacts

_NANOSECONDS: Final = 1_000_000_000


class DateFrom(StrEnum):
    """Where the date of a file comes from."""

    EXIF = "exif"
    VIDEO = "video"


class Flag(StrEnum):
    """A label derived from raw measures and the `[inventory]` thresholds."""

    BLURRY = "blurry"
    SMALL = "small"
    DARK = "dark"
    BRIGHT = "bright"


@dataclass(frozen=True, slots=True)
class InventoryContext:
    """What every line needs: host paths, duplicate digests, thresholds, video zone."""

    mapper: HostPathMapper
    shared: Mapping[str, SharedDigest]
    settings: InventorySettings
    zone: tzinfo


@dataclass(frozen=True, slots=True)
class Entry:
    """A media file of the index, ready to be written as one row."""

    file: IndexedFile
    kind: MediaKind
    context: InventoryContext

    @property
    def visual(self) -> VisualFacts | None:
        """What the image looks like, when it was decoded.

        Returns:
            The visual facts, or None.
        """
        return self.file.facts.visual

    @property
    def metadata(self) -> MediaMetadata | None:
        """What the file says about itself.

        Returns:
            The metadata, or None.
        """
        return self.file.facts.metadata

    @property
    def modified(self) -> datetime:
        """The modification time, in UTC, without a zone (Excel has none).

        Returns:
            The naive UTC date.
        """
        moment = datetime.fromtimestamp(self.file.mtime_ns / _NANOSECONDS, UTC)
        return moment.replace(tzinfo=None)

    def dated(self) -> tuple[datetime, DateFrom] | None:
        """When the photo or video was taken, read as `classify` reads it.

        Returns:
            The naive local date and its source, or None.
        """
        visual, metadata = self.visual, self.metadata
        if visual is not None and (taken := exif_date(visual.taken_at)):
            return taken, DateFrom.EXIF
        if self.kind is MediaKind.VIDEO and metadata is not None:
            recorded = video_date(metadata.recorded_at, self.context.zone)
            return (recorded, DateFrom.VIDEO) if recorded else None
        return None

    def shared(self) -> SharedDigest | None:
        """The group of identical files this one belongs to.

        Returns:
            Its group and number of copies, or None for a file without a copy.
        """
        digest = self.file.facts.full_digest
        return self.context.shared.get(digest) if digest else None

    def quality(self) -> tuple[Flag, ...] | None:
        """Blurry or small, after the `[inventory]` thresholds.

        Returns:
            The flags (empty: fine), or None for a file never decoded.
        """
        visual, limits = self.visual, self.context.settings
        if visual is None:
            return None
        flags = [Flag.BLURRY] if visual.sharpness < limits.blurry_below else []
        if min(visual.width, visual.height) < limits.small_below:
            flags.append(Flag.SMALL)
        return tuple(flags)

    def exposure(self) -> tuple[Flag, ...] | None:
        """Dark or bright, after the `[inventory]` thresholds.

        Returns:
            The flags (empty: fine), or None without exposure measures.
        """
        metadata, limits = self.metadata, self.context.settings
        if metadata is None or metadata.brightness is None:
            return None
        dark = (metadata.dark_share or 0) > limits.clipped_above
        bright = (metadata.bright_share or 0) > limits.clipped_above
        flags = []
        if metadata.brightness < limits.dark_below or dark:
            flags.append(Flag.DARK)
        if metadata.brightness > limits.bright_above or bright:
            flags.append(Flag.BRIGHT)
        return tuple(flags)


def entry_of(file: IndexedFile, context: InventoryContext) -> Entry | None:
    """Describe a file of the index, when it is a photo, a RAW file or a video.

    Args:
        file: The file and its facts.
        context: What every line needs.

    Returns:
        The entry, or None for another file (asked for with `--ext`).
    """
    kind = media_kind(file.path)
    return Entry(file, kind, context) if kind is not None else None
