"""Translated names of the bands and date sources: console and workbook."""

from __future__ import annotations

from media_hygiene.classify.carry_models import EditSheet, LostEdit, LostWhy
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


def lost_line(lost: LostEdit) -> str:
    """Describe an edit that was not carried over, in one line.

    Args:
        lost: The edit.

    Returns:
        E.g. `Files: a.jpg: '2016/Fair' (the file is gone)`, translated.
    """
    sheets = {
        EditSheet.FILES: _("Files"),
        EditSheet.EVENTS: _("Events"),
        EditSheet.CATEGORIES: _("Categories"),
    }
    reasons = {
        (LostWhy.GONE, EditSheet.FILES): _("the file is gone"),
        (LostWhy.GONE, EditSheet.EVENTS): _("its files are gone"),
        (LostWhy.GONE, EditSheet.CATEGORIES): _("this category is no longer proposed"),
        (LostWhy.MERGED, EditSheet.EVENTS): _(
            "merged with another named event, whose name wins"
        ),
    }
    if lost.why is LostWhy.CONFLICT:
        reasons[lost.why, lost.sheet] = _(
            "chosen in the review page, then edited otherwise in the workbook, "
            "whose value was carried over"
        )
    why = reasons.get((lost.why, lost.sheet), _("the value cannot be used"))
    return _("{sheet}: {key}: '{value}' ({why})").format(
        sheet=sheets[lost.sheet], key=lost.key, value=lost.value, why=why
    )
