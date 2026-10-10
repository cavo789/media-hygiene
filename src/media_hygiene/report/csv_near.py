"""The near duplicates and re-encoded videos in `plan.csv`: every group, never capped.

An audit lists them as `clean --tier near` would move them; a clean run with the tier
lists them as moved. Their groups are numbered after the exact-duplicate groups.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.report.near_reasons import near_why

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.plan.similar_models import NearDecision
    from media_hygiene.scan.models import MediaFile


@dataclass(frozen=True, slots=True)
class NearLine:
    """One file of a near-duplicate group, and what the plan does to it."""

    file: MediaFile
    action: str
    group: str
    detail: str = ""


def near_lines(findings: AuditFindings) -> Iterator[NearLine]:
    """One line per file of every near-duplicate group, the kept version first.

    Args:
        findings: The audit; its plan holds the groups a `--tier near` clean moves.

    Yields:
        The lines.
    """
    plan, similar = findings.plan, findings.similar
    numbers = count(len(plan.decisions) + 1)
    moving = bool(plan.near)
    move = _("move to the quarantine") if moving else _("move with --tier near")
    for decision in similar.near:
        why = near_why(decision, lambda file: similar.visuals[file.path].pixels)
        detail = _("Near duplicate: {why}").format(why=why)
        yield from _group(decision, str(next(numbers)), (move, detail))
    for decision in similar.videos:
        why = near_why(decision, lambda file: similar.video_looks[file.path].pixels)
        detail = _("Re-encoded video: {why}").format(why=why)
        yield from _group(decision, str(next(numbers)), (move, detail))


def _group(
    decision: NearDecision, group: str, wording: tuple[str, str]
) -> Iterator[NearLine]:
    """The lines of one group.

    Args:
        decision: The group.
        group: Its number in the file.
        wording: The action of a copy, and why the kept version is kept.

    Yields:
        The kept version, its copies, then the copies in protected folders.
    """
    move, detail = wording
    yield NearLine(decision.keeper, _("keep"), group, detail)
    same = _("Same picture and sound as the kept video: only the metadata differ.")
    for file in decision.removable:
        yield NearLine(
            file, move, group, same if file.path in decision.same_stream else ""
        )
    for file in decision.protected:
        yield NearLine(file, _("protected, kept"), group)
