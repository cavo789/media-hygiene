"""A keyboard review in progress: the shots set aside, saved after every decision.

The decisions file is shared with the report's folder-pair decisions: a review keeps
the `pairs` it finds there and writes its own `bursts`, every series listed from the
start (`todo` until seen). Reopened on the same folders, it resumes where it stopped.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from media_hygiene.errors import DecisionsError
from media_hygiene.report.decisions import write_decisions
from media_hygiene.review.session_file import (
    choice_problem,
    proven,
    read_back,
    series_decision,
)
from media_hygiene.review.session_series import proposed_shots, resumed, with_choice
from media_hygiene.review.shots import shot_places
from media_hygiene.review.views import ReviewState, preview_key

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.config.review_settings import ReviewSettings
    from media_hygiene.plan.burst_proposals import ProposalLimits
    from media_hygiene.plan.similar_models import BurstSeries
    from media_hygiene.report.decisions import DecisionsFile
    from media_hygiene.review.place import DecisionsPlace
    from media_hygiene.review.session_file import FileProof
    from media_hygiene.review.strictness import Strictness
    from media_hygiene.review.views import StateBuilder


@dataclass(frozen=True, slots=True)
class ReviewSource:
    """What a review is about: the burst series, how to show them, the file to write."""

    bursts: tuple[BurstSeries, ...]
    builder: StateBuilder
    target: Path
    place: DecisionsPlace
    hidden: frozenset[str] = frozenset()  # host shots of series not shown, kept (0630)


class ReviewSession:  # pylint: disable=too-many-instance-attributes
    """The series under review and the shots set aside, in memory and on disk."""

    def __init__(self, source: ReviewSource, base: DecisionsFile) -> None:
        """Resume the series of `base` seen earlier that still match the audit.

        Args:
            source: The series and the decisions file.
            base: What the decisions file holds already.
        """
        self._source = source
        self._base = base
        self._states = tuple(source.builder.series(burst) for burst in source.bursts)
        shots = (file for burst in source.bursts for file in burst.shots)
        self._previews = {preview_key(file): file.path for file in shots}
        self._places = shot_places(source.bursts, source.builder.mapper)
        self._discarded, self.dropped = resumed(source, base, self._places)
        self.strictness: Strictness[ReviewSettings] | None = None  # set by the service

    @property
    def place(self) -> DecisionsPlace:
        """The decisions file, for `clean --decisions` and on the host.

        Returns:
            Its names.
        """
        return self._source.place

    @property
    def progress(self) -> tuple[int, int]:
        """How far the review went.

        Returns:
            The number of series with shots set aside, and of shots set aside.
        """
        aside = [shots for shots in self._discarded.values() if shots]
        return len(aside), sum(map(len, aside))

    @property
    def seen(self) -> tuple[int, int]:
        """How many series were seen, out of how many.

        Returns:
            The series seen, and every series.
        """
        return len(self._discarded), len(self._states)

    def state(self) -> ReviewState:
        """Describe every series and the shots set aside, for the page.

        Returns:
            The state.
        """
        return ReviewState(
            decisions_file=self.place.argument,
            decisions_place=self.place.host,
            series=tuple(
                with_choice(state, self._discarded.get(number))
                for number, state in enumerate(self._states)
            ),
        )

    def retune(self, limits: ProposalLimits) -> dict[str, str]:
        """Propose again with other thresholds; the choices made stay.

        Args:
            limits: The thresholds.

        Returns:
            The file name of each shot proposed in a series still to see, by path.
        """
        builder = replace(self._source.builder, limits=limits)
        self._source = replace(self._source, builder=builder)
        self._states = tuple(builder.series(burst) for burst in self._source.bursts)
        return proposed_shots(self._states, self._discarded)

    def preview_source(self, key: str) -> Path | None:
        """Find the shot a preview shows.

        Args:
            key: The preview key, from the page.

        Returns:
            The shot, in the container, or None for an unknown key.
        """
        return self._previews.get(key)

    def save(self) -> None:
        """Write the decisions file: every series, seen or still to see."""
        write_decisions(self._source.target, self.decisions())

    def on_disk(self) -> FileProof:
        """Read the decisions file back from the disk.

        Returns:
            What it holds, series by series.
        """
        return read_back(self._source.target, self._places)

    def decide(self, choices: Mapping[int, frozenset[int] | None]) -> FileProof:
        """Record choices, save them in one write, then read the file back.

        Args:
            choices: Ranks of the shots set aside, by series rank (none: seen and
                kept whole; None: back to still to see).

        Returns:
            Those series, as the file read back from the disk holds them.

        Raises:
            DecisionsError: An unknown series or shot, a shot of a protected folder,
                or a file that does not hold the choices once saved.
        """
        for series, discarded in choices.items():
            problem = choice_problem(self._source, series, discarded)
            if problem is not None:
                raise DecisionsError(problem)
        for series, discarded in choices.items():
            if discarded is None:
                self._discarded.pop(series, None)
            else:
                self._discarded[series] = discarded
        self.save()
        mapper, bursts = self._source.builder.mapper, self._source.bursts
        expected = {
            series: series_decision(mapper, bursts[series].shots, discarded)
            for series, discarded in choices.items()
        }
        return proven(self.on_disk(), expected)

    def decisions(self) -> DecisionsFile:
        """Build the decisions file: the pairs found in it, every series in order.

        Returns:
            The decisions, in host paths.
        """
        mapper, bursts = self._source.builder.mapper, self._source.bursts
        listed = tuple(
            series_decision(mapper, burst.shots, self._discarded.get(number))
            for number, burst in enumerate(bursts)
        )
        hidden = self._source.hidden
        kept = tuple(
            old
            for old in self._base.bursts
            if not hidden.isdisjoint((*old.kept, *old.discarded))
        )
        return self._base.model_copy(update={"bursts": listed + kept})
