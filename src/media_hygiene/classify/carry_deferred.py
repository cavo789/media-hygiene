"""Read back the edits a narrowed run kept for later: the newer workbook wins."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.classify.carry_models import EditSheet, LostEdit, LostWhy
from media_hygiene.classify.carry_types import typed_text
from media_hygiene.classify.workbook.edits import Edits
from media_hygiene.classify.workbook.salvage_models import Notes

if TYPE_CHECKING:
    from media_hygiene.classify.carry_types import CarrySource


def with_deferred(source: CarrySource) -> CarrySource:
    """Add the edits the previous plan kept for later; the workbook wins over them.

    Args:
        source: The previous workbook.

    Returns:
        The same, its plan holding the rows and events of the kept edits too.
    """
    plan = source.plan
    if plan is None or plan.deferred is None:
        return source
    kept = plan.deferred
    rows = {row.id for row in plan.rows}
    events = {event.id for event in plan.events}
    salvaged = source.salvaged
    edits, notes = salvaged.edits, salvaged.notes
    paths = {row.id: row.path for row in (*plan.rows, *kept.rows)}
    replaced = (
        LostEdit(
            sheet=EditSheet.FILES,
            key=paths.get(key, key),
            value=typed_text(value),
            why=LostWhy.REPLACED,
        )
        for key, value in kept.edits.files.items()
        if key in edits.files and edits.files[key] != value
    )
    merged = Edits(
        files={**kept.edits.files, **edits.files},
        events={**kept.edits.events, **edits.events},
        categories={**kept.edits.categories, **edits.categories},
        file_cells=edits.file_cells,
    )
    widened = plan.model_copy(
        update={
            "rows": (*plan.rows, *(row for row in kept.rows if row.id not in rows)),
            "events": (
                *plan.events,
                *(event for event in kept.events if event.id not in events),
            ),
            "deferred": None,
        }
    )
    return replace(
        source,
        plan=widened,
        salvaged=replace(
            salvaged,
            edits=merged,
            notes=Notes(
                {**kept.notes.files, **notes.files},
                {**kept.notes.events, **notes.events},
                {**kept.notes.categories, **notes.categories},
            ),
            invalid=(*salvaged.invalid, *replaced),
        ),
    )
