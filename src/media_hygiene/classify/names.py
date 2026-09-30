"""Translated names of the bands and date sources: console and workbook."""

from __future__ import annotations

from media_hygiene.classify.models import Band, DateSource
from media_hygiene.i18n import _


def band_name(band: Band) -> str:
    """The translated name of a band.

    Args:
        band: A band.

    Returns:
        Its name.
    """
    names = {
        Band.SURE: _("Sure"),
        Band.UNSURE: _("To check"),
        Band.MANUAL: _("To sort"),
        Band.UNDATED: _("Undated"),
        Band.STAY: _("Left as they are"),
    }
    return names[band]


def source_name(source: DateSource | None) -> str:
    """The translated name of a date source.

    Args:
        source: Where a date comes from, or None (no date).

    Returns:
        Its name.
    """
    names = {
        DateSource.EXIF: _("camera (EXIF)"),
        DateSource.VIDEO: _("video tags"),
        DateSource.NAME: _("file name"),
        DateSource.FOLDER: _("folder name"),
        DateSource.MTIME: _("date on the disk"),
    }
    return names[source] if source else ""
