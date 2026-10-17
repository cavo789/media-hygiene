"""`clean --decisions`: check the burst shots a review set aside against the audit.

Every series with shots set aside must still be one series of the audit, and none of
them may lie in a protected folder. Anything else refuses the whole file, like a stale
pair. A series still to see (`todo`), or kept whole, moves nothing: it is never checked.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _, ngettext
from media_hygiene.plan.similar_models import BurstChoice
from media_hygiene.report.burst_decisions import BurstStatus
from media_hygiene.review.shots import match_burst, shot_places
from media_hygiene.services.policy import keep_policy

if TYPE_CHECKING:
    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.plan.similar_models import BurstSeries
    from media_hygiene.report.burst_decisions import BurstDecision
    from media_hygiene.review.shots import MatchedBurst
    from media_hygiene.services.runtime import Runtime


def burst_choices(
    runtime: Runtime, findings: AuditFindings, bursts: tuple[BurstDecision, ...]
) -> tuple[BurstChoice, ...]:
    """Translate the reviewed burst series into shots of this audit.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        bursts: The reviews of burst series, from the decisions file.

    Returns:
        The shots kept and set aside, in container paths.

    Raises:
        DecisionsError: A series changed since the review, or a shot set aside lies
            in a protected folder.
    """
    _tell_todo(runtime, bursts)
    series = findings.similar.bursts
    places = shot_places(series, runtime.mapper)
    seen = (d for d in bursts if d.status is BurstStatus.DONE)
    matched = [(decision, match_burst(decision, places)) for decision in seen]
    matched = [(d, match) for d, match in matched if match or d.discarded]
    stale = [decision for decision, match in matched if match is None]
    if stale:
        message = ngettext(
            "{count} reviewed burst series no longer matches the audit, e.g. {path}.",
            "{count} reviewed burst series no longer match the audit, e.g. {path}.",
            len(stale),
        )
        raise DecisionsError(
            message.format(
                count=len(stale), path=(*stale[0].kept, *stale[0].discarded)[0]
            ),
            _("Files changed since the review: run 'review' again."),
        )
    choices = tuple(_choice(series, match) for _decision, match in matched if match)
    policy = keep_policy(runtime.settings, runtime.mapper)
    for choice in choices:
        locked = [file for file in choice.discarded if policy.is_protected(file)]
        if locked:
            message = _("{path} is in a protected folder: it is never moved.")
            raise DecisionsError(
                message.format(path=runtime.mapper.to_host(locked[0].path))
            )
    return choices


def _tell_todo(runtime: Runtime, bursts: tuple[BurstDecision, ...]) -> None:
    """Say how many series the review has not shown yet: their shots stay.

    Args:
        runtime: Settings, mount points and output.
        bursts: The reviews of burst series, from the decisions file.
    """
    todo = sum(decision.status is BurstStatus.TODO for decision in bursts)
    if todo:
        message = ngettext(
            "{count} burst series not reviewed yet: its shots stay.",
            "{count} burst series not reviewed yet: their shots stay.",
            todo,
        )
        runtime.output.info(message.format(count=todo))


def _choice(series: tuple[BurstSeries, ...], match: MatchedBurst) -> BurstChoice:
    """Turn ranks in a series into its shots.

    Args:
        series: The burst series of the audit.
        match: The review, as ranks in one of them.

    Returns:
        The shots kept and set aside.
    """
    shots = series[match.series].shots
    return BurstChoice(
        kept=tuple(shots[rank] for rank in sorted(match.kept)),
        discarded=tuple(shots[rank] for rank in sorted(match.discarded)),
    )
