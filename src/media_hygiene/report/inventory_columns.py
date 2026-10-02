"""The columns of the inventory: a translated header, a value, a format, a width.

Values are typed (numbers, dates) so that sorting and filtering work in Excel whatever
the regional settings; the CSV export writes them as text.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.report.inventory_labels import (
    camera_of,
    date_source_label,
    flags_label,
    flash_label,
    format_of,
    integrity_label,
    kind_label,
    time_zone,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import datetime

    from media_hygiene.report.inventory_entries import Entry

type Cell = str | int | float | datetime | None

DATE_FORMAT: Final = "yyyy-mm-dd hh:mm:ss"
_BYTES: Final = "#,##0"
_SHARE: Final = "0.0%"
_NARROW, _WIDE, _PATH = 10, 18, 60


@dataclass(frozen=True, slots=True)
class Column:
    """One column: its header, how to read its value from an entry, how to show it."""

    header: str
    value: Callable[[Entry], Cell]
    number_format: str | None = None
    width: int = _NARROW


def _meta(name: str) -> Callable[[Entry], Cell]:
    """Read one field of the metadata.

    Args:
        name: The field of `MediaMetadata`.

    Returns:
        The reader: the value, or None.
    """

    def read(entry: Entry) -> Cell:
        """Read the field.

        Args:
            entry: The file.

        Returns:
            Its value, or None.
        """
        value: Cell = getattr(entry.metadata, name, None)
        return value

    return read


def _host(entry: Entry) -> str:
    """The file, as the user knows it on the host."""
    return entry.context.mapper.to_host(entry.file.path)


def _folder(entry: Entry) -> str:
    """Its folder, on the host."""
    return entry.context.mapper.to_host(entry.file.path.parent)


def _flash(entry: Entry) -> str | None:
    """Whether the flash fired."""
    return flash_label(entry.metadata.flash if entry.metadata else None)


def _date(entry: Entry) -> datetime | None:
    """The date the file was taken."""
    dated = entry.dated()
    return dated[0] if dated else None


def _source(entry: Entry) -> str | None:
    """Where that date comes from."""
    dated = entry.dated()
    return date_source_label(dated[1]) if dated else None


def _year(entry: Entry) -> int | None:
    """The year it was taken, for statistics per year."""
    dated = entry.dated()
    return dated[0].year if dated else None


def _size(entry: Entry, index: int) -> int | None:
    """The width (0) or the height (1) in pixels."""
    visual, metadata = entry.visual, entry.metadata
    if visual is not None:
        return (visual.width, visual.height)[index]
    if metadata is not None:
        return (metadata.width, metadata.height)[index]
    return None


def _group(entry: Entry) -> int | None:
    """The number of its group of identical files."""
    shared = entry.shared()
    return shared.group if shared else None


def _copies(entry: Entry) -> int | None:
    """How many identical files its group holds."""
    shared = entry.shared()
    return shared.copies if shared else None


def _broken_detail(entry: Entry) -> str | None:
    """What the decoder said about a broken file."""
    return entry.file.facts.broken_detail or None


def columns() -> tuple[Column, ...]:
    """Every column, its header in the active language.

    Returns:
        The columns, in order.
    """
    return (
        Column(_("File"), _host, width=_PATH),
        Column(_("Folder"), _folder, width=_PATH),
        Column(_("Name"), lambda e: e.file.path.name, width=_WIDE * 2),
        Column(_("Kind"), lambda e: kind_label(e.kind)),
        Column(_("Size (bytes)"), lambda e: e.file.size, _BYTES, _WIDE),
        Column(_("Modified (UTC)"), lambda e: e.modified, DATE_FORMAT, _WIDE),
        Column(_("Date taken"), _date, DATE_FORMAT, _WIDE),
        Column(_("Date from"), _source),
        Column(_("Year"), _year),
        Column(_("Time zone"), time_zone),
        Column(_("Camera"), camera_of, width=_WIDE * 2),
        Column(_("Lens"), _meta("lens"), width=_WIDE),
        Column(_("Focal length (mm)"), _meta("focal_length")),
        Column(_("Exposure time (s)"), _meta("exposure_time")),
        Column(_("F-number"), _meta("f_number")),
        Column(_("ISO"), _meta("iso")),
        Column(_("Flash"), _flash),
        Column(_("Width"), lambda e: _size(e, 0)),
        Column(_("Height"), lambda e: _size(e, 1)),
        Column(_("Sharpness"), lambda e: e.visual.sharpness if e.visual else None),
        Column(_("Quality"), lambda e: flags_label(e.quality())),
        Column(_("Format"), format_of),
        Column(_("JPEG quality"), _meta("jpeg_quality")),
        Column(_("Brightness"), _meta("brightness")),
        Column(_("Black pixels"), _meta("dark_share"), _SHARE),
        Column(_("White pixels"), _meta("bright_share"), _SHARE),
        Column(_("Exposure"), lambda e: flags_label(e.exposure())),
        Column(_("Latitude"), _meta("latitude")),
        Column(_("Longitude"), _meta("longitude")),
        Column(_("Altitude (m)"), _meta("altitude")),
        Column(_("Place (video tag)"), _meta("location"), width=_WIDE),
        Column(_("Duration (s)"), _meta("duration")),
        Column(_("Codec"), _meta("codec")),
        Column(_("Frame rate"), _meta("frame_rate")),
        Column(_("Bit rate"), _meta("bit_rate"), _BYTES, _WIDE),
        Column(_("Rating"), _meta("rating")),
        Column(_("Software"), _meta("software"), width=_WIDE),
        Column(_("Integrity"), integrity_label, width=_WIDE),
        Column(_("Decoder message"), _broken_detail, width=_WIDE * 2),
        Column(_("SHA-256"), lambda e: e.file.facts.full_digest, width=_WIDE * 2),
        Column(_("Duplicate group"), _group),
        Column(_("Copies"), _copies),
    )
