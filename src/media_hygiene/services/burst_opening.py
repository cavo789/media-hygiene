"""The session of a burst review, opened on all the series or on some of them (0630).

The page of an import's new photos shows only their series: the decisions of the
library's other series, read from the same file, are written back untouched.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.review.place import decisions_place
from media_hygiene.review.session import ReviewSession, ReviewSource
from media_hygiene.review.strictness import Strictness, ThresholdPlace
from media_hygiene.review.views import StateBuilder
from media_hygiene.services.burst_carry import resume_bursts
from media_hygiene.services.policy import keep_policy, proposal_limits
from media_hygiene.services.review_file import first_save

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.services.runtime import Runtime

BURST_SECTION: Final = ("review",)
BURST_KEYS: Final = ("propose_aside_below", "identical_below")


@dataclass(frozen=True, slots=True)
class BurstOpening:
    """The series to show, the decisions file, the series left out but kept."""

    findings: AuditFindings  # its bursts: the series shown
    target: Path  # the decisions file, in the container
    hidden: frozenset[str] = frozenset()  # host shots whose decisions stay as they are


def open_bursts(runtime: Runtime, opening: BurstOpening) -> ReviewSession:
    """Start the review of the series, resuming the decisions file.

    The file is written at once, every series listed: `todo` until seen.

    Args:
        runtime: Settings, mount points and output.
        opening: The series, the file, the series left out.

    Returns:
        The session.

    Raises:
        DecisionsError: The file is not a decisions file, was made on other
            folders, or cannot be written.
    """
    mapper, findings, target = runtime.mapper, opening.findings, opening.target
    builder = StateBuilder(
        mapper,
        keep_policy(runtime.settings, mapper),
        findings.similar,
        proposal_limits(runtime.settings.review),
    )
    place = decisions_place(mapper, runtime.locations.reports_dir, target)
    bursts = findings.similar.bursts
    source = ReviewSource(bursts, builder, target, place, opening.hidden)
    session = ReviewSession(source, resume_bursts(runtime, findings, target))
    session.strictness = Strictness(
        ThresholdPlace(runtime.locations.config_file, BURST_SECTION, BURST_KEYS),
        runtime.settings.review,
        lambda review: session.retune(proposal_limits(review)),
    )
    first_save(session.save)
    return session
