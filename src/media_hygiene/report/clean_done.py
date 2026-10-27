"""What a clean did, and what it left for later: the two blocks of a clean report.

A clean report tells the past (0309): the near duplicates, re-encoded videos and
burst shots it shows are the ones this run moved, minus the files the run skipped
or failed on; the groups it did not touch are only counted, with the command that
decides them.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from media_hygiene.constants import RunKind

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.plan.similar_models import NearDecision, SimilarFindings
    from media_hygiene.report.views import ReportRecord


@dataclass(frozen=True, slots=True)
class CleanAsked:
    """What the options of a clean asked for, beyond exact copies."""

    near: bool = False  # `--tier near` or `near-all`
    bursts: bool = False  # `--decisions` with burst shots or files set aside


@dataclass(frozen=True, slots=True)
class CleanDone:  # pylint: disable=too-many-instance-attributes
    """The counts of the two blocks: done by this run, then left untouched."""

    copies: int = 0
    copies_bytes: int = 0
    near: int = 0  # near-duplicate and re-encoded video copies moved
    bursts: int = 0  # burst shots set aside
    broken: int = 0
    near_left: int = 0  # groups of near duplicates and videos not touched
    bursts_left: int = 0  # burst series not touched
    asked: CleanAsked = CleanAsked()


def asked_flags(asked: CleanAsked | None) -> dict[str, bool]:
    """Name a clean's options as `summary.json` stores them.

    Args:
        asked: The options, None for an audit.

    Returns:
        The `near_tier` and `bursts_decided` fields.
    """
    asked = asked or CleanAsked()
    return {"near_tier": asked.near, "bursts_decided": asked.bursts}


def _not_done(record: ReportRecord) -> frozenset[Path]:
    outcome = record.outcome
    if outcome is None:
        return frozenset()
    return frozenset(item.path for item in (*outcome.failed, *outcome.skipped))


def _moved(
    decisions: tuple[NearDecision, ...], not_done: frozenset[Path]
) -> tuple[NearDecision, ...]:
    kept = (
        replace(d, removable=tuple(f for f in d.removable if f.path not in not_done))
        for d in decisions
    )
    return tuple(decision for decision in kept if decision.removable)


def shown_similar(record: ReportRecord) -> SimilarFindings:
    """Pick the similar pictures a report shows.

    Args:
        record: What the report is written from.

    Returns:
        Every finding for an audit; for a clean, only the groups it moved.
    """
    similar = record.findings.similar
    if record.kind is not RunKind.CLEAN:
        return similar
    moved = _moved(record.findings.plan.near, _not_done(record))
    videos = {decision.keeper.path for decision in similar.videos}
    return replace(
        similar,
        near=tuple(d for d in moved if d.keeper.path not in videos),
        videos=tuple(d for d in moved if d.keeper.path in videos),
        bursts=(),
    )


def clean_done(record: ReportRecord) -> CleanDone | None:
    """Count what a clean did, from its plan less what it skipped or failed on.

    Args:
        record: What the report is written from.

    Returns:
        The counts, or None for an audit.
    """
    if record.kind is not RunKind.CLEAN:
        return None
    plan, similar = record.findings.plan, record.findings.similar
    not_done = _not_done(record)
    copies = [f for d in plan.decisions for f in d.removable if f.path not in not_done]
    moved = _moved(plan.near, not_done)
    touched = {decision.keeper.path for decision in moved}
    groups = (*similar.near, *similar.videos)
    return CleanDone(
        copies=len(copies),
        copies_bytes=sum(file.size for file in copies),
        near=sum(len(decision.removable) for decision in moved),
        bursts=sum(
            1 for c in plan.bursts for f in c.discarded if f.path not in not_done
        ),
        broken=sum(1 for item in plan.broken if item.file.path not in not_done),
        near_left=sum(1 for d in groups if d.keeper.path not in touched),
        bursts_left=max(0, len(similar.bursts) - len(plan.bursts)),
        asked=record.asked or CleanAsked(),
    )
