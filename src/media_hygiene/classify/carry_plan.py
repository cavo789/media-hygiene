"""Write the carried edits into the new plan: a carried edit is a human edit.

The rows an edit reaches take the folder and the band it gives (sure, as for any edit
of the user), with the reason `carried-over`. The edits stay in the yellow cells of the
new workbook too: `sort` applies them again, to the same folders.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.classify.carry_models import CarryRecord
from media_hygiene.classify.models import SortReason
from media_hygiene.classify.workbook.edits import resolve

if TYPE_CHECKING:
    from media_hygiene.classify.carry_types import Carried, CarrySource
    from media_hygiene.classify.plan_file import ClassifyPlan

# A human edit is as sure as it gets.
_HUMAN_SCORE: Final = 100


def with_carried(
    plan: ClassifyPlan, carried: Carried, source: CarrySource
) -> ClassifyPlan:
    """The plan once the carried edits are applied to its rows.

    Args:
        plan: The new plan.
        carried: The edits carried over, keyed for it.
        source: Where they come from.

    Returns:
        The plan, its rows reached by an edit marked `carried-over`, and the record.
    """
    rows = tuple(
        row
        if decision.folder == row.folder and decision.band is row.band
        else row.model_copy(
            update={
                "folder": decision.folder,
                "band": decision.band,
                "reason": SortReason.CARRIED_OVER,
                "score": _HUMAN_SCORE,
                "rule": "",
            }
        )
        for row, decision in zip(plan.rows, resolve(plan, carried.edits), strict=True)
    )
    record = CarryRecord(
        workbook=source.workbook,
        saved_at=source.saved_at,
        edits=carried.count,
        notes=carried.note_count,
        split=carried.split,
        lost=carried.lost,
    )
    return plan.model_copy(update={"rows": rows, "carried": record})
