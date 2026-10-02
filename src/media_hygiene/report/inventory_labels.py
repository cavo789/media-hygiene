"""The words of the inventory: kinds, date sources, labels, integrity, yes or no."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import MediaKind
from media_hygiene.i18n import _
from media_hygiene.report.inventory_entries import DateFrom, Flag
from media_hygiene.report.reasons import broken_reason_label

if TYPE_CHECKING:
    from media_hygiene.report.inventory_entries import Entry

_FLASH_FIRED: Final = 1  # bit 0 of the EXIF Flash tag
_LIST: Final = ", "


def kind_label(kind: MediaKind) -> str:
    """Name a kind of media file.

    Args:
        kind: The kind.

    Returns:
        Photo, RAW or video, translated.
    """
    labels = {
        MediaKind.IMAGE: _("photo"),
        MediaKind.RAW: _("RAW"),
        MediaKind.VIDEO: _("video"),
    }
    return labels.get(kind, kind.value)


def date_source_label(source: DateFrom) -> str:
    """Name where a date comes from.

    Args:
        source: The source.

    Returns:
        The translated name.
    """
    return _("EXIF") if source is DateFrom.EXIF else _("video tags")


def flags_label(flags: tuple[Flag, ...] | None) -> str | None:
    """Spell the labels of a file, "ok" when none applies.

    Args:
        flags: The labels, or None when nothing was measured.

    Returns:
        The translated labels, or None.
    """
    if flags is None:
        return None
    names = {
        Flag.BLURRY: _("blurry"),
        Flag.SMALL: _("small"),
        Flag.DARK: _("dark"),
        Flag.BRIGHT: _("bright"),
    }
    return _LIST.join(names[flag] for flag in flags) if flags else _("ok")


def integrity_label(entry: Entry) -> str:
    """Say whether the file could be read.

    Args:
        entry: The file.

    Returns:
        Healthy, not checked, or why it is broken.
    """
    integrity = entry.file.facts.integrity
    if integrity is None:
        return _("not checked")
    if integrity.broken_reason is None:
        return _("healthy")
    return broken_reason_label(integrity.broken_reason)


def flash_label(flash: int | None) -> str | None:
    """Say whether the flash fired.

    Args:
        flash: The EXIF Flash tag.

    Returns:
        Yes or no, or None when not recorded.
    """
    if flash is None:
        return None
    return _("yes") if flash & _FLASH_FIRED else _("no")


def time_zone(entry: Entry) -> str | None:
    """The offset the file records with its date.

    Args:
        entry: The file.

    Returns:
        `+02:00` for a photo with an EXIF offset or a video with a local date, or None.
    """
    metadata = entry.metadata
    if metadata is None:
        return None
    if metadata.offset:
        return metadata.offset
    if not metadata.created_local:
        return None
    try:
        offset = datetime.fromisoformat(metadata.created_local).strftime("%:z")
    except ValueError:
        return None
    return offset or None


def camera_of(entry: Entry) -> str | None:
    """The device: EXIF make and model of a photo, tags of a video.

    Args:
        entry: The file.

    Returns:
        Its name, or None.
    """
    if entry.visual is not None and entry.visual.camera:
        return entry.visual.camera
    metadata = entry.metadata
    parts = (metadata.make, metadata.model) if metadata else ()
    return " ".join(part for part in parts if part) or None


def format_of(entry: Entry) -> str:
    """The format Pillow names, else the extension.

    Args:
        entry: The file.

    Returns:
        `JPEG`, `MP4`...
    """
    metadata = entry.metadata
    if metadata is not None and metadata.file_format:
        return metadata.file_format
    return entry.file.path.suffix.lstrip(".").upper()
