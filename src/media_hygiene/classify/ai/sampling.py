"""Which photos the model sees: a few per event, only where stronger signals are silent.

A file decided by a folder, a date, a path, a camera or a kind is never asked about;
neither is a file left as it is, nor an undated one. The undecided files of an event
make one unit: its samples, the sharpest of each part of its span, answer for all of
them, videos included. A lone file is a unit of its own. Photos already described are
preferred as samples, so that new settings recutting the events cost no new night.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.ai.models import Candidate, Unit
from media_hygiene.classify.models import Band, SortReason
from media_hygiene.constants import MediaKind
from media_hygiene.scan.filters import media_kind

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable, Sequence
    from pathlib import Path

    from media_hygiene.classify.models import Proposal
    from media_hygiene.config.classify_ai import AiSettings

# What no rule decided: the model may speak.
SILENT: Final = frozenset(
    {
        SortReason.NO_SIGNAL,
        SortReason.DATE_ONLY,
        SortReason.OTHER_CATEGORY,
        SortReason.PREVIOUS_GUESS,
    }
)
_SKIPPED_BANDS: Final = frozenset({Band.STAY, Band.UNDATED})
_PICTURES: Final = frozenset({MediaKind.IMAGE, MediaKind.RAW})


def units_of(proposals: Iterable[Proposal], ai: AiSettings) -> tuple[Unit, ...]:
    """Group the files no stronger signal decided into units, largest first.

    Args:
        proposals: The proposals of a run without `subject` rules.
        ai: `[classify.ai]`: the smallest side a photo must have.

    Returns:
        The units that have at least one photo the model may see.
    """
    grouped: dict[str, list[Proposal]] = defaultdict(list)
    for proposal in proposals:
        if proposal.reason in SILENT and proposal.band not in _SKIPPED_BANDS:
            grouped[proposal.event_id or str(proposal.file.path)].append(proposal)
    units = (
        Unit(
            key,
            tuple(p.file.path for p in members),
            tuple(c for p in members if (c := _candidate(p, ai.min_edge))),
        )
        for key, members in grouped.items()
    )
    found = [unit for unit in units if unit.candidates]
    found.sort(key=lambda unit: (-len(unit.members), unit.key))
    return tuple(found)


def _candidate(proposal: Proposal, min_edge: int) -> Candidate | None:
    """A photo the model may see.

    Args:
        proposal: The proposal of one file.
        min_edge: The smallest side, in pixels.

    Returns:
        The candidate, or None for a video, an undecoded or a tiny picture.
    """
    file, dating = proposal.file, proposal.dating
    visual = file.visual
    if visual is None or dating is None or media_kind(file.path) not in _PICTURES:
        return None
    if min(visual.width, visual.height) < min_edge:
        return None
    return Candidate(file.path, dating.when, visual.sharpness)


def choose_samples(
    unit: Unit, count: int, described: Collection[Path]
) -> tuple[Path, ...]:
    """Spread `count` samples across the span of a unit.

    Args:
        unit: The unit.
        count: How many samples (`samples_per_event`); 0: every photo.
        described: The photos already in the cache.

    Returns:
        One photo per part of the span: described first, then the sharpest.
    """
    ordered = sorted(unit.candidates, key=lambda c: (c.when, str(c.path)))
    if count <= 0 or count >= len(ordered):
        return tuple(c.path for c in ordered)
    known = [c for c in ordered if c.path in described]
    if len(known) >= count:
        ordered = known  # a recut event: what is described is enough
    parts = _split(ordered, count)
    return tuple(
        max(part, key=lambda c: (c.path in described, c.sharpness, str(c.path))).path
        for part in parts
    )


def _split(ordered: Sequence[Candidate], count: int) -> list[Sequence[Candidate]]:
    """Cut a sorted list into `count` parts of nearly equal length.

    Args:
        ordered: The candidates, in date order.
        count: How many parts, fewer than the candidates.

    Returns:
        The parts, in order.
    """
    size = len(ordered)
    bounds = [size * index // count for index in range(count + 1)]
    return [ordered[bounds[i] : bounds[i + 1]] for i in range(count)]
