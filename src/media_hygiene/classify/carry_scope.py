"""Edits outside a narrowed run: kept for later, not lost while their files exist.

`classify --year 2015` (or `--path`) proposes nothing for the other files. Their edits
in the previous workbook are kept in the new plan (`DeferredEdits`); the next carry-over
reads them back (`carry_deferred`). A file really gone is still listed as gone.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from media_hygiene.classify.carry_rows import row_map
from media_hygiene.classify.plan_deferred import DeferredEdits
from media_hygiene.classify.workbook.edits import Edits
from media_hygiene.classify.workbook.salvage_models import Notes, Salvaged

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from media_hygiene.classify.carry_types import CarrySource
    from media_hygiene.classify.plan_file import ClassifyPlan


@dataclass(frozen=True, slots=True)
class ScopeCheck:
    """Whether the new run was narrowed, and how to tell that a file still exists."""

    narrowed: bool  # `--year` or `--path`
    exists: Callable[[str], bool]  # host path → still on the disk


def split_scope(
    source: CarrySource, new: ClassifyPlan, check: ScopeCheck
) -> tuple[CarrySource, DeferredEdits | None]:
    """Set aside the edits of the files a narrowed run left out.

    Args:
        source: The previous workbook, its kept edits included.
        new: The new plan.
        check: Whether the run was narrowed; which files still exist.

    Returns:
        The edits to carry over now, and those kept for later (None: none).
    """
    old = source.plan
    if not check.narrowed or old is None:
        return source, None
    matched = row_map(old, new)
    outside = {
        row.id: row
        for row in old.rows
        if row.id not in matched
        and row.id not in source.applied
        and check.exists(row.path)
    }
    if not outside:
        return source, None
    events = tuple(
        event for event in old.events if _left_out(event.rows, matched, outside)
    )
    salvaged = source.salvaged
    later, now = _split(
        (salvaged.edits, salvaged.notes),
        (
            set(outside),
            {event.id for event in events},
            {row.category for row in outside.values()} - set(new.categories()),
        ),
    )
    if Salvaged("", *later).empty:
        return source, None
    named = {*later[0].files, *later[1].files}
    named |= {row for event in events for row in event.rows}
    rows = tuple(row for key, row in outside.items() if key in named)
    kept_now = replace(salvaged, edits=now[0], notes=now[1])
    return replace(source, salvaged=kept_now), DeferredEdits.of((rows, events), later)


def keep_deferred(plan: ClassifyPlan, deferred: DeferredEdits | None) -> ClassifyPlan:
    """Keep the edits set aside in the new plan, and count them in its record.

    Args:
        plan: The new plan, carried edits applied.
        deferred: The edits kept for later.

    Returns:
        The plan.
    """
    if deferred is None:
        return plan
    record = plan.carried
    if record is not None:
        record = record.model_copy(update={"deferred": deferred.count})
    return plan.model_copy(update={"deferred": deferred, "carried": record})


def _left_out(
    rows: tuple[str, ...], matched: Mapping[str, str], outside: Mapping[str, object]
) -> bool:
    """Tell whether the run left out every file of an event, one of them still there.

    Args:
        rows: The event's previous rows.
        matched: The previous rows found in the new plan.
        outside: The previous rows left out by the run, their files still there.

    Returns:
        True when the event's edit is kept for later.
    """
    return (
        bool(rows)
        and not any(row in matched for row in rows)
        and any(row in outside for row in rows)
    )


def _split(
    typed: tuple[Edits, Notes], keys: tuple[set[str], set[str], set[str]]
) -> tuple[tuple[Edits, Notes], tuple[Edits, Notes]]:
    """Split edits and notes by the rows, events and categories set aside.

    Args:
        typed: The edits and the notes.
        keys: The rows, the events and the categories set aside.

    Returns:
        Those set aside, then the others.
    """
    (edits, notes), (rows, events, categories) = typed, keys
    files, file_notes = _parts(edits.files, rows), _parts(notes.files, rows)
    event_edits = _parts(edits.events, events)
    event_notes = _parts(notes.events, events)
    names = _parts(edits.categories, categories)
    name_notes = _parts(notes.categories, categories)
    later = (
        Edits(files[0], event_edits[0], names[0]),
        Notes(file_notes[0], event_notes[0], name_notes[0]),
    )
    now = (
        Edits(files[1], event_edits[1], names[1], edits.file_cells),
        Notes(file_notes[1], event_notes[1], name_notes[1]),
    )
    return later, now


def _parts[T](
    values: Mapping[str, T], keys: set[str]
) -> tuple[dict[str, T], dict[str, T]]:
    """Split a mapping by its keys.

    Args:
        values: The mapping.
        keys: The keys set aside.

    Returns:
        The entries set aside, then the others.
    """
    inside = {key: value for key, value in values.items() if key in keys}
    return inside, {key: value for key, value in values.items() if key not in keys}
