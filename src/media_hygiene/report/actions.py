"""What an audit lets the user do, each action with its gain and its effort.

At most three lines: the identical copies (no risk, one command), the near duplicates
(the sure groups, and those to look at), the burst series (optional). The effort is a
fixed estimate per group to look at or series, the pace measured on the review page.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.plan.models import AuditFindings

NEAR_GROUP_SECONDS: Final = 30  # to compare two pictures and choose
BURST_SERIES_SECONDS: Final = 40  # to look at a series in 'review' and choose
_SECONDS_PER_MINUTE: Final = 60


@dataclass(frozen=True, slots=True)
class ActionCommands:
    """The full command of each action, ready to paste."""

    clean: str = ""
    near: str = ""
    review: str = ""
    near_review: str = ""  # `review --near`: the groups to look at, in the browser


@dataclass(frozen=True, slots=True)
class AuditAction:
    """One thing the user can do now: an icon, what it gains and costs, its command."""

    icon: str
    text: str
    command: str = ""


def effort(seconds: int) -> str:
    """Round an estimate up to the minute, the way people say it.

    Args:
        seconds: The estimate.

    Returns:
        E.g. `2 min` or `1 h 05 min`; never less than one minute.
    """
    minutes = max(1, math.ceil(seconds / _SECONDS_PER_MINUTE))
    hours, minutes = divmod(minutes, _SECONDS_PER_MINUTE)
    if hours:
        return f"{hours} h {minutes:02d} min"
    return f"{minutes} min"


def sure_count(sure: int) -> str:
    """Count the sure groups, the adjective agreeing with their own number.

    A sentence counting several things takes its plural from one of them only:
    `1 sûrs` came from the total of groups, so the sure ones carry their own plural.

    Args:
        sure: How many groups are sure.

    Returns:
        E.g. `1 sure`; `1 sûr`, `3 sûrs` in French.
    """
    return ngettext("{count} sure", "{count} sure", sure).format(
        count=human_number(sure)
    )


def audit_actions(
    findings: AuditFindings, commands: ActionCommands
) -> tuple[AuditAction, ...]:
    """List what the audit found worth doing, most rewarding and safest first.

    Args:
        findings: The audit.
        commands: The command of each action.

    Returns:
        Up to three actions.
    """
    plan, similar = findings.plan, findings.similar
    actions: list[AuditAction] = []
    if plan.decisions:
        copies = ngettext(
            "{count} identical copy, {size}: no risk, one command.",
            "{count} identical copies, {size}: no risk, one command.",
            plan.removable_count,
        )
        actions.append(
            AuditAction(
                "✅",
                copies.format(
                    count=human_number(plan.removable_count),
                    size=human_size(plan.reclaimable),
                ),
                commands.clean,
            )
        )
    groups = len(similar.groups)
    if groups:
        sure = similar.sure_groups
        near = ngettext(
            "{count} group of near duplicates: {sure}, {look} to look at "
            "(~{effort} in 'review --near'); 'clean --tier near' moves the sure ones.",
            "{count} groups of near duplicates: {sure}, {look} to look at "
            "(~{effort} in 'review --near'); 'clean --tier near' moves the sure ones.",
            groups,
        )
        text = near.format(
            count=human_number(groups),
            sure=sure_count(sure),
            look=human_number(groups - sure),
            effort=effort((groups - sure) * NEAR_GROUP_SECONDS),
        )
        command = commands.near_review if groups > sure else commands.near
        actions.append(AuditAction("👀", text, command))
    series = len(similar.bursts)
    if series:
        bursts = ngettext(
            "{count} burst series: optional, ~{effort} in 'review'; a series not "
            "reviewed is kept whole.",
            "{count} burst series: optional, ~{effort} in 'review'; the series not "
            "reviewed are kept whole.",
            series,
        )
        text = bursts.format(
            count=human_number(series), effort=effort(series * BURST_SERIES_SECONDS)
        )
        actions.append(AuditAction("🎞️", text, commands.review))
    return tuple(actions)


def actions_title() -> str:
    """The heading of the actions, in the terminal and in the report.

    Returns:
        The translated heading.
    """
    return _("What you can do")
