"""The series of a review as the page and the session read them (0537)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.report.burst_decisions import BurstStatus
from media_hygiene.review.session_file import choice_problem
from media_hygiene.review.shots import match_burst

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from media_hygiene.report.decisions import DecisionsFile
    from media_hygiene.review.session import ReviewSource
    from media_hygiene.review.shots import ShotPlace
    from media_hygiene.review.views import SeriesState


def with_choice(state: SeriesState, choice: frozenset[int] | None) -> SeriesState:
    """Describe a series with the shots set aside, and whether it was seen.

    Args:
        state: The series.
        choice: Its shots set aside; None: still to see.

    Returns:
        Its state.
    """
    return state.model_copy(
        update={
            "discarded": tuple(sorted(choice or ())),
            "reviewed": choice is not None,
        }
    )


def proposed_shots(
    states: Sequence[SeriesState], seen: Mapping[int, object]
) -> dict[str, str]:
    """Name the shots proposed aside in the series still to see.

    Args:
        states: Every series.
        seen: The series seen, by rank.

    Returns:
        The file name of each shot, by path.
    """
    return {
        f"{shot.folder}/{shot.name}": shot.name
        for number, item in enumerate(states)
        if number not in seen
        for shot in item.shots
        if shot.proposed
    }


def resumed(
    source: ReviewSource, base: DecisionsFile, places: Mapping[str, ShotPlace]
) -> tuple[dict[int, frozenset[int]], int]:
    """Find the series of a decisions file that still match the audit.

    Args:
        source: The series.
        base: What the decisions file holds.
        places: Every shot of the audit.

    Returns:
        The shots set aside by series seen, and how many reviews were dropped.
    """
    found: dict[int, frozenset[int]] = {}
    dropped = 0
    for decision in base.bursts:
        match = match_burst(decision, places)
        if decision.status is BurstStatus.TODO:
            continue  # listed again by the session, from the audit
        if match is None or choice_problem(source, match.series, match.discarded):
            dropped += 1
            continue
        found[match.series] = match.discarded
    return found, dropped
