"""`sort --trial`: sort a sample first, one month or one folder, then the rest (0526).

The plan is cut to the sample's rows, like `--event`: one journaled, undoable run.
Those rows then count as moved for the plan, so the same `sort` without `--trial`
moves only the rest.
"""

from __future__ import annotations

import re
from dataclasses import replace
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.sort_resume import moved_rows
from media_hygiene.errors import WorkbookError
from media_hygiene.i18n import _
from media_hygiene.paths.host_paths import is_within
from media_hygiene.services.sort_event import only_rows

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.sort_inputs import SortInputs
    from media_hygiene.services.sort_models import Prepared

LATEST: Final = "latest"  # `--trial latest`: the latest month with photos
_MONTH: Final = re.compile(r"^\d{4}-\d{2}$")
_MONTH_LENGTH: Final = len("2024-05")


def latest_month(inputs: SortInputs) -> str:
    """The latest month with a file to move: one where all stays would show nothing.

    Args:
        inputs: The plan and its edits.

    Returns:
        `YYYY-MM`; empty when no dated file moves.
    """
    months = {
        row.date[:_MONTH_LENGTH]
        for row in inputs.plan.rows
        if row.date and row.values is not None and row.folder and not row.in_place
    }
    return max(months, default="")


def first_sample(
    runtime: Runtime, prepared: Prepared, prepare: Callable[[SortInputs], Prepared]
) -> Prepared | None:
    """The latest month as a sample, when this is a plan's first sort (0640).

    Args:
        runtime: Settings, mount points and output.
        prepared: The whole sort, ready.
        prepare: Prepares the sample as the whole sort was.

    Returns:
        The sample; None once a run moved files of the plan, or when the month
        is all there is to move: a trial would be the sort itself.
    """
    inputs = prepared.inputs
    journal = runtime.locations.journal_dir
    if moved_rows(journal, inputs.plan.plan_id) or not latest_month(inputs):
        return None
    sample = prepare(only_trial(inputs, LATEST, runtime.mapper))
    wanted = len(sample.plan.moves)
    return sample if 0 < wanted < len(prepared.plan.moves) else None


def only_trial(inputs: SortInputs, sample: str, mapper: HostPathMapper) -> SortInputs:
    """Cut the plan to a sample: `latest`, a month `YYYY-MM`, or a folder.

    Args:
        inputs: The plan and its edits.
        sample: What `--trial` named.
        mapper: Host and container paths, to read a folder given either way.

    Returns:
        The same inputs, the plan holding only the sample's rows.

    Raises:
        WorkbookError: No file of the plan lies in the sample.
    """
    rows = inputs.plan.rows
    if sample == LATEST or _MONTH.match(sample):
        month = latest_month(inputs) if sample == LATEST else sample
        ids = (
            frozenset(row.id for row in rows if row.date and row.date.startswith(month))
            if month
            else frozenset()
        )
    else:
        folder = mapper.to_container(sample)
        ids = frozenset(
            row.id for row in rows if is_within(mapper.to_container(row.path), folder)
        )
    if not ids:
        message = _("No file of the plan in the sample {sample}.").format(sample=sample)
        tip = _("Give 'latest', a month such as 2024-05, or a folder of the plan.")
        raise WorkbookError(message, tip)
    return replace(only_rows(inputs, ids), trial=True)
