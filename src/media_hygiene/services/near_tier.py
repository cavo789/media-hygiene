"""`clean --tier near` and `near-all`: the near duplicates a clean moves, as decided.

`--tier near` moves the sure groups, `--tier near-all` every group; the decisions of
`review --near` (`--decisions`) override both, group by group. A decision is checked
against the audit first: a group that changed since, or a swap that would move a file
of a protected folder, refuses the whole file.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_number
from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _, ngettext
from media_hygiene.plan.near_review import NearAction, NearVerdict, selected
from media_hygiene.services.policy import keep_policy

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.plan.models import AuditFindings, CleanPlan
    from media_hygiene.plan.near_review import NearSelection
    from media_hygiene.plan.similar_models import NearDecision
    from media_hygiene.report.near_decisions import NearGroupDecision
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class NearRequest:
    """The audit, and which of its near duplicates the clean moves."""

    findings: AuditFindings
    selection: NearSelection


def with_near(runtime: Runtime, plan: CleanPlan, request: NearRequest) -> CleanPlan:
    """Add the near duplicates and re-encoded videos the clean moves to the plan.

    Near duplicates are moved to the quarantine, never deleted: `ensure_ready` with
    `near=True` has checked it is mounted. What stays in place is said.

    Args:
        runtime: Settings, mount points and output.
        plan: The feasible plan.
        request: The audit, the tier and the decisions.

    Returns:
        The plan, the near duplicates it moves included.
    """
    groups = request.findings.similar.groups
    moved = selected(groups, request.selection)
    verdicts = request.selection.verdicts or {}
    if verdicts:
        actions = [verdict.action for verdict in verdicts.values()]
        runtime.output.info(
            _(
                "Your decisions — near-duplicate groups as planned: {planned}, "
                "another version kept: {swap}, none kept: {none}, left alone: {leave}."
            ).format(
                planned=actions.count(NearAction.PLANNED),
                swap=actions.count(NearAction.SWAP),
                none=actions.count(NearAction.NONE),
                leave=actions.count(NearAction.LEAVE),
            )
        )
    left = sum(
        verdicts.get(group.keeper.path) is None and group.sure is None
        for group in groups
    )
    if left and not request.selection.every:
        message = ngettext(
            "{count} group of near duplicates to check stays in place: decide it "
            "with 'review --near', or --tier near-all moves it too.",
            "{count} groups of near duplicates to check stay in place: decide them "
            "with 'review --near', or --tier near-all moves them too.",
            left,
        )
        runtime.output.info(message.format(count=human_number(left)))
    return replace(plan, near=moved)


def near_verdicts(
    runtime: Runtime,
    findings: AuditFindings,
    decided: tuple[NearGroupDecision, ...],
) -> Mapping[Path, NearVerdict]:
    """Check the decisions of `review --near` against this audit, and translate them.

    Args:
        runtime: Settings, mount points and output.
        findings: The audit just run.
        decided: The `near` decisions of the file.

    Returns:
        Each decision, by the container path of the version the audit keeps.

    Raises:
        DecisionsError: A group changed since the review, or a swap (or a group
            kept none of) would move a file of a protected folder.
    """
    mapper = runtime.mapper
    groups = {
        (mapper.to_host(group.keeper.path), _copies(runtime, group)): group
        for group in findings.similar.groups
    }
    stale = [d for d in decided if (d.kept, tuple(sorted(d.copies))) not in groups]
    if stale:
        message = ngettext(
            "{count} decided group of near duplicates changed since, e.g. {kept}.",
            "{count} decided groups of near duplicates changed since, e.g. {kept}.",
            len(stale),
        )
        raise DecisionsError(
            message.format(count=len(stale), kept=stale[0].kept),
            _("Files changed since the review: run 'review --near' again."),
        )
    verdicts: dict[Path, NearVerdict] = {}
    for decision in decided:
        group = groups[decision.kept, tuple(sorted(decision.copies))]
        verdicts[group.keeper.path] = _verdict(runtime, group, decision)
    return MappingProxyType(verdicts)


def _copies(runtime: Runtime, group: NearDecision) -> tuple[str, ...]:
    """The copies a group moves, in sorted host paths.

    Args:
        runtime: Settings, mount points and output.
        group: The group.

    Returns:
        Their host paths.
    """
    return tuple(sorted(runtime.mapper.to_host(file.path) for file in group.removable))


def _verdict(
    runtime: Runtime, group: NearDecision, decision: NearGroupDecision
) -> NearVerdict:
    """Translate one decision, refusing to move the kept version when protected.

    Args:
        runtime: Settings, mount points and output.
        group: The group, as the audit plans it.
        decision: The decision on it.

    Returns:
        The verdict, in container paths.

    Raises:
        DecisionsError: The version the audit keeps lies in a protected folder.
    """
    if decision.action not in {NearAction.SWAP, NearAction.NONE}:
        return NearVerdict(decision.action)
    if keep_policy(runtime.settings, runtime.mapper).is_protected(group.keeper):
        message = _("{path} is in a protected folder: it is never moved.")
        raise DecisionsError(message.format(path=decision.kept))
    if decision.action is NearAction.NONE:
        return NearVerdict(NearAction.NONE)
    mapper = runtime.mapper
    keep = next(f for f in group.removable if mapper.to_host(f.path) == decision.keep)
    return NearVerdict(NearAction.SWAP, keep)
