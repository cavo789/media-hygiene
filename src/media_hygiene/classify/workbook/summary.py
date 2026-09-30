"""The Summary sheet: progress first, then the counts that tell where the work is."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.names import band_name, source_name
from media_hygiene.classify.worklist import WORK_BANDS
from media_hygiene.console.formatting import human_share
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.classify.plan_file import ClassifyPlan
    from media_hygiene.classify.workbook.rows import Row
    from media_hygiene.classify.workbook.sheets import Labels

_TOP_CATEGORIES: Final = 30


def summary_headers(labels: Labels) -> Row:
    """The header row of the Summary sheet: its free Notes column is the third.

    Args:
        labels: The translated sheet names.

    Returns:
        Them.
    """
    return (labels.summary, None, _("Notes"))


def summary_rows(plan: ClassifyPlan) -> list[Row]:
    """Progress, then the counts per band, year, category, reason and date source.

    Args:
        plan: The plan.

    Returns:
        Label/value rows; a label alone is a title.
    """
    rows = plan.rows
    in_place = sum(1 for row in rows if row.in_place)
    left = sum(1 for row in rows if row.band in WORK_BANDS)
    lines: list[Row] = [
        (_("Already in place"), human_share(in_place, len(rows))),
        (_("To check or to sort"), left),
        (_("Edit only the yellow cells, then save; nothing moves before 'sort'."),),
        (),
        (_("Bands"),),
    ]
    lines += _counts(Counter(band_name(row.band) for row in rows))
    lines += [(), (_("Years"),)]
    lines += sorted(_counts(Counter(str(r.values.year) for r in rows if r.values)))
    lines += [(), (_("Categories"),)]
    categories = Counter(row.category for row in rows if row.category)
    lines += _counts(categories)[:_TOP_CATEGORIES]
    lines += [(), (_("Reasons"),)]
    lines += _counts(Counter(row.reason.value for row in rows))
    lines += [(), (_("Dates from"),)]
    lines += _counts(Counter(source_name(row.date_source) for row in rows))
    return lines


def _counts(counter: Counter[str]) -> list[Row]:
    """Label/count rows, the largest first.

    Args:
        counter: The counts.

    Returns:
        The rows.
    """
    return [(label or "-", count) for label, count in counter.most_common()]
