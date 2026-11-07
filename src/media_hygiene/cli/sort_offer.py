"""The question before a first `sort`: try the latest month first (0640)."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from media_hygiene.console.sort_view import sort_table
from media_hygiene.i18n import _
from media_hygiene.services.sort_trial import first_sample, latest_month

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.sort_inputs import SortInputs
    from media_hygiene.services.sort_models import Prepared


def offer_trial(
    runtime: Runtime, prepared: Prepared, prepare: Callable[[SortInputs], Prepared]
) -> Prepared | None:
    """Offer the latest month before the whole sort: asked in a terminal only.

    Args:
        runtime: Settings, mount points and output.
        prepared: The whole sort, ready.
        prepare: Prepares the sample as the whole sort was.

    Returns:
        The sample to run; None: go on with the question of the whole sort.
    """
    if not runtime.settings.sort.confirm or not sys.stdin.isatty():
        return None
    sample = first_sample(runtime, prepared, prepare)
    if sample is None:
        return None
    output = runtime.output
    output.show(sort_table(sample))
    question = _(
        "First sort: try on the latest month, {month}, {count} of {total} files? "
        "Then look, and sort the rest or undo."
    )
    asked = question.format(
        month=latest_month(prepared.inputs),
        count=len(sample.plan.moves),
        total=len(prepared.plan.moves),
    )
    return sample if output.confirm(asked) else None
