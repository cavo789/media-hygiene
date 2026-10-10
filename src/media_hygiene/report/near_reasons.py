"""Why a version of near duplicates was kept, in one sentence for the report and CSV.

Each group says it: the highest resolution, a larger (less compressed) file, or, when
the sizes differ by less than 1 %, the usual rule that chose, the size gap shown.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_size
from media_hygiene.constants import NearReason
from media_hygiene.i18n import _
from media_hygiene.report.reasons import keep_reason_label

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.plan.similar_models import NearDecision
    from media_hygiene.scan.models import MediaFile


def near_why(decision: NearDecision, pixels: Callable[[MediaFile], int]) -> str:
    """Say why the kept version won.

    Args:
        decision: The group.
        pixels: The displayed resolution of a version.

    Returns:
        The translated sentence.
    """
    keeper = decision.keeper
    peers = [
        file.size
        for file in (*decision.removable, *decision.protected)
        if pixels(file) == pixels(keeper)
    ]
    if decision.reason is NearReason.RESOLUTION or not peers:
        return _("Kept: the highest resolution.")
    if decision.reason is NearReason.SIZE:
        return _(
            "Kept: the same resolution, a larger file by {gap} (less compressed)."
        ).format(gap=human_size(keeper.size - max(peers)))
    gap = max(abs(keeper.size - size) for size in peers)
    return _(
        "The same resolution and sizes {gap} apart (under 1 %): the size says "
        "nothing, the usual rules chose: {rule}."
    ).format(gap=human_size(gap), rule=keep_reason_label(decision.rule))
