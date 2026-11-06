"""`sort --trial`: sort a sample first, one month or one folder, then the rest (0526).

The plan is cut to the sample's rows, like `--event`: one journaled, undoable run.
Those rows then count as moved for the plan, so the same `sort` without `--trial`
moves only the rest.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import WorkbookError
from media_hygiene.i18n import _
from media_hygiene.paths.host_paths import is_within
from media_hygiene.services.sort_event import only_rows

if TYPE_CHECKING:
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.services.sort_inputs import SortInputs

LATEST: Final = "latest"  # `--trial latest`: the latest month with photos
_MONTH: Final = re.compile(r"^\d{4}-\d{2}$")
_MONTH_LENGTH: Final = len("2024-05")


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
        months = {row.date[:_MONTH_LENGTH] for row in rows if row.date}
        month = max(months, default="") if sample == LATEST else sample
        ids = frozenset(
            row.id for row in rows if row.date and row.date.startswith(month)
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
    return only_rows(inputs, ids)
