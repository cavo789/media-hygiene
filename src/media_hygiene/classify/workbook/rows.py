"""The content of each sheet: headers and rows, editable cells last."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.models import Band
from media_hygiene.classify.names import band_name, source_name
from media_hygiene.classify.worklist import work_list
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.classify.plan_file import ClassifyPlan, PlanRow
    from media_hygiene.classify.workbook.sheets import Labels

type Row = tuple[str | int | float | None, ...]

_SAMPLES: Final = 3
_FOLDERS: Final = 3


def file_headers() -> Row:
    """The headers of the Files sheet (`FileColumn` order).

    Returns:
        Them.
    """
    return (
        _("Id"),
        _("Root"),
        _("Folder"),
        _("Name"),
        _("Date"),
        _("Date from"),
        _("Event"),
        _("Band"),
        _("Reason"),
        _("Proposed folder"),
        _("Final folder"),
        _("Notes"),
    )


def file_rows(plan: ClassifyPlan, labels: Labels) -> list[Row]:
    """One row per file, in path order.

    Args:
        plan: The plan.
        labels: The drop-down values.

    Returns:
        The rows.
    """
    return [
        (
            row.id,
            row.root,
            row.parent,
            row.name,
            (row.date or "").replace("T", " "),
            source_name(row.date_source),
            row.event_id,
            band_name(row.band),
            f"{row.reason.value} ({row.score})",
            _folder(row, labels),
            None,
            None,
        )
        for row in plan.rows
    ]


def event_headers() -> Row:
    """The headers of the Events sheet (`EventColumn` order).

    Returns:
        Them.
    """
    return (
        _("Id"),
        _("Dates"),
        _("Files"),
        _("To check or to sort"),
        _("Share of the work, cumulated"),
        _("Folders"),
        _("Proposed folder"),
        _("Sample names"),
        _("Name"),
        _("Category"),
        _("Notes"),
    )


def event_rows(plan: ClassifyPlan, labels: Labels) -> list[Row]:
    """One row per event, in the order of the work list.

    Args:
        plan: The plan.
        labels: The drop-down values.

    Returns:
        The rows.
    """
    return [
        (
            item.event.id,
            item.event.span,
            len(item.rows),
            item.undecided,
            round(item.cumulated, 3) if item.undecided else None,
            " | ".join(item.folders[:_FOLDERS]),
            _folder(item.proposal, labels),
            ", ".join(row.name for row in item.rows[:_SAMPLES]),
            None,
            None,
            None,
        )
        for item in work_list(plan)
    ]


def category_headers() -> Row:
    """The headers of the Categories sheet (`CategoryColumn` order).

    Returns:
        Them.
    """
    return (
        _("Category"),
        _("Files"),
        _("To check"),
        _("New name"),
        _("Confirm the files to check"),
        _("Notes"),
    )


def category_rows(plan: ClassifyPlan) -> list[Row]:
    """One row per proposed category, the largest first.

    Args:
        plan: The plan.

    Returns:
        The rows.
    """
    unsure = Counter(row.category for row in plan.rows if row.band is Band.UNSURE)
    return [
        (category, count, unsure[category], None, None, None)
        for category, count in plan.categories().items()
    ]


def _folder(row: PlanRow, labels: Labels) -> str:
    """The proposed folder as shown: relative, or "(stay where it is)".

    Args:
        row: A row.
        labels: The drop-down values.

    Returns:
        The text.
    """
    return labels.stay if row.folder is None else row.folder
