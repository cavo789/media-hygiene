"""The audit's actions the journal brings: files back, files gone (0216, 0224)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import ngettext
from media_hygiene.plan.returned import returned_moves, returned_size
from media_hygiene.report.action_models import AuditAction

if TYPE_CHECKING:
    from media_hygiene.plan.models import CleanPlan


def returned_action(plan: CleanPlan, command: str) -> AuditAction | None:
    """The files set aside before that came back, if any (0216).

    Args:
        plan: The audit's plan.
        command: The `clean` command, which sets them aside again.

    Returns:
        The action, or None.
    """
    count = len(returned_moves(plan))
    if not count:
        return None
    back = ngettext(
        "{count} photo or video you had set aside is back ({size}): 'clean' sets "
        "it aside again.",
        "{count} photos and videos you had set aside are back ({size}): 'clean' "
        "sets them aside again.",
        count,
    )
    size = human_size(returned_size(plan))
    return AuditAction("↩️", back.format(count=human_number(count), size=size), command)


def gone_action(count: int, command: str) -> AuditAction:
    """The files gone since the last audit, to confirm (0224).

    Args:
        count: How many wait for an answer.
        command: `review --gone`.

    Returns:
        The action.
    """
    gone = ngettext(
        "{count} photo or video has disappeared since the last audit (deleted in the "
        "Explorer?): say if you deleted it on purpose, so that media-hygiene sets it "
        "aside if it comes back.",
        "{count} photos and videos have disappeared since the last audit (deleted in "
        "the Explorer?): say which ones you deleted on purpose, so that media-hygiene "
        "sets them aside if they come back.",
        count,
    )
    return AuditAction("🗑️", gone.format(count=human_number(count)), command)
