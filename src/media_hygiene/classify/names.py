"""Translated names of the bands, reasons and date sources: console and workbook."""

from __future__ import annotations

from media_hygiene.classify.carry_models import EditSheet, LostEdit, LostWhy
from media_hygiene.classify.models import Band, DateSource, SortReason
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


def reason_name(reason: SortReason) -> str:
    """The translated name of a reason, shown when no rule of the user decided.

    Args:
        reason: A reason.

    Returns:
        Its name.
    """
    names = {
        SortReason.EXISTING_FOLDER: _("Existing folder"),
        SortReason.PERSON_FOLDER: _("Folder of a person"),
        SortReason.EVENT_NEIGHBOUR: _("Event of a named folder"),
        SortReason.CALENDAR: _("Days of every year"),
        SortReason.DATE_RANGE: _("Date range"),
        SortReason.KIND: _("Kind of file"),
        SortReason.PATH: _("Path"),
        SortReason.CAMERA: _("Camera"),
        SortReason.SUBJECT: _("Subject"),
        SortReason.PLACE: _("Personal place"),
        SortReason.PLACE_NEIGHBOUR: _("Event at a personal place"),
        SortReason.TRIP: _("Trip"),
        SortReason.TRIP_NEIGHBOUR: _("Event of a trip"),
        SortReason.FOLDER_TOWN: _("Town of the folder"),
        SortReason.PERSON: _("Person"),
        SortReason.OTHER_CATEGORY: _("Other category"),
        SortReason.DATE_ONLY: _("Date only"),
        SortReason.NO_SIGNAL: _("No signal"),
        SortReason.UNDATED: _("Undated"),
        SortReason.LEFT_AS_IS: _("Left as it is"),
        SortReason.CARRIED_OVER: _("Edit carried over from the workbook"),
        SortReason.PREVIOUS_GUESS: _("Previous guess, already in place"),
    }
    return names[reason]


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
        DateSource.TAKEOUT: _("Google Photos record (.json)"),
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
    if lost.why is LostWhy.REPLACED:
        reasons[lost.why, lost.sheet] = _(
            "kept by a run with --year or --path, then edited otherwise in the "
            "workbook, whose value was carried over"
        )
    if lost.why is LostWhy.CONFLICT:
        reasons[lost.why, lost.sheet] = _(
            "chosen in the review page, then edited otherwise in the workbook, "
            "whose value was carried over"
        )
    why = reasons.get((lost.why, lost.sheet), _("the value cannot be used"))
    return _("{sheet}: {key}: '{value}' ({why})").format(
        sheet=sheets[lost.sheet], key=lost.key, value=lost.value, why=why
    )
