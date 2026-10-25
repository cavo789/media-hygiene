"""`sort --event <id>`, *Sort this event now*: one event sorted, the rest left.

The plan is cut to the rows of one event; everything else is the whole `sort`: the same
guards (a persistent `/journal`, no `:ro` data mount), the same journal, `undo` and
manifest, the index following the moves. Those rows then count as moved for the plan:
a later `sort` of the whole workbook skips them.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.errors import WorkbookError
from media_hygiene.i18n import _
from media_hygiene.review.sort_now import SortedNow
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.sort import SortService
from media_hygiene.services.sort_inputs import find_workbook, load_inputs

if TYPE_CHECKING:
    from media_hygiene.review.sort_batch import SortBatchSession
    from media_hygiene.review.sort_now import Sorter
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.sort_inputs import SortInputs
    from media_hygiene.services.sort_models import SortResult


def only_event(inputs: SortInputs, event_id: str) -> SortInputs:
    """Cut the plan to the files of one event.

    Args:
        inputs: The plan and its edits.
        event_id: The event, as the Events sheet and the review page name it.

    Returns:
        The same inputs, the plan holding only that event's rows.

    Raises:
        WorkbookError: The plan has no such event.
    """
    rows = tuple(row for row in inputs.plan.rows if row.event_id == event_id)
    if not event_id or not rows:
        message = _("The plan has no event {event}.").format(event=event_id)
        tip = _("Copy its id from the first column of the Events sheet.")
        raise WorkbookError(message, tip)
    return replace(inputs, plan=inputs.plan.model_copy(update={"rows": rows}))


def sort_event(runtime: Runtime, workbook: str, event_id: str) -> SortResult | None:
    """Sort the files of one event now, without asking: the page asked already.

    Args:
        runtime: Settings, mount points and output.
        workbook: The workbook (host or container path).
        event_id: The event.

    Returns:
        The run, or None when every file of the event is already in place.

    Raises:
        MediaHygieneError: Sorting is not possible here (no `/journal`, a `:ro`
            mount), or the workbook or the event cannot be read.
    """
    service = SortService(runtime, NullProgress())
    service.ensure_ready()
    inputs = only_event(
        load_inputs(runtime, find_workbook(runtime, workbook)), event_id
    )
    prepared = service.prepare(inputs)
    if not prepared.plan.groups:
        return None
    return service.execute(prepared, lambda: False)


def sorter_of(runtime: Runtime, session: SortBatchSession) -> Sorter:
    """*Sort this event now* for the review page: the run, then the event read back.

    Args:
        runtime: Settings, mount points and output.
        session: The review: its workbook, and the rows moved to read again.

    Returns:
        A function sorting one event, by its id.
    """

    def run(event_id: str) -> SortedNow:
        """Sort one event, then describe it from the journal and the disk.

        Args:
            event_id: The event.

        Returns:
            The run and the event, sorted.
        """
        result = sort_event(runtime, session.hosts[0], event_id)
        session.refresh_moved()
        view = session.event(event_id)
        if result is None:
            return SortedNow(run_id="", moved=0, verified=0, intact=True, view=view)
        manifest = result.manifest
        return SortedNow(
            run_id=result.run_id,
            moved=manifest.moved,
            verified=manifest.verified,
            intact=manifest.intact,
            view=view,
        )

    return run
