"""Why a version of near duplicates was kept, and how sure the group is, for the report.

Each group says it: the highest resolution, a larger (less compressed) file, or, when
the sizes differ by less than 1 %, the usual rule that chose, the size gap shown.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_size
from media_hygiene.constants import NearReason
from media_hygiene.i18n import _
from media_hygiene.plan.similar_models import SureReason
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
    if decision.reason is NearReason.CHOSEN:
        return _("Kept: your choice in 'review --near'.")
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


def level_text(decision: NearDecision) -> str:
    """Say whether a group is sure, and why, or worth a look.

    Args:
        decision: The group.

    Returns:
        The translated sentence.
    """
    match decision.sure:
        case SureReason.SAME_STREAM:
            return _("Sure: the very picture and sound, only the metadata differ.")
        case SureReason.SAME_LOOK:
            return _("Sure: identical fingerprints, from the same camera.")
        case SureReason.MESSAGING_COPY:
            return _(
                "Sure: a smaller copy in a messaging or e-mail folder, taken at the "
                "same moment."
            )
        case None:
            return _("To check: compare the copies with the kept version.")


@dataclass(frozen=True, slots=True)
class GroupNote:
    """What the report says of a group beyond its files: why, how sure, the gain."""

    why: str  # why the kept version won
    level: str  # sure, and why, or to check
    sure: bool  # moved by `--tier near` without a look
    gain: int = 0  # bytes its copies free
    running: int = 0  # % of the space freed by it and the groups above (`gain_order`)


def group_note(
    decision: NearDecision, pixels: Callable[[MediaFile], int], running: int
) -> GroupNote:
    """Say why a group's kept version won, how sure the group is, what it frees.

    Args:
        decision: The group.
        pixels: The displayed resolution of a version.
        running: The share of the space freed by it and the groups shown above.

    Returns:
        The note.
    """
    return GroupNote(
        why=near_why(decision, pixels),
        level=level_text(decision),
        sure=decision.sure is not None,
        gain=decision.reclaimable,
        running=running,
    )
