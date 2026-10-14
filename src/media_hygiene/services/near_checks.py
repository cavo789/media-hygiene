"""Find near duplicates, then check what the hashes cannot see: colours, same streams.

Perceptual hashes are computed in grey. The pictures and videos they find alike are
measured for colour, and the search runs again with it: a black and white edit then
stays apart from its colour original. Measuring only the candidates keeps an audit
light, and the index keeps each measure (`index.measures`): a later audit measures
only the files that are new or changed.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import TYPE_CHECKING

from media_hygiene.index.measures import Measure
from media_hygiene.plan.near_levels import with_levels
from media_hygiene.plan.similar import SimilarInputs, find_similar
from media_hygiene.scan.colour import colours
from media_hygiene.scan.stopwatch import Stage
from media_hygiene.services.same_streams import same_streams

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from media_hygiene.index.measures import MeasureStore
    from media_hygiene.plan.keeper import KeepPolicy
    from media_hygiene.plan.similar_models import (
        NearDecision,
        SimilarFindings,
    )
    from media_hygiene.scan.colour import ColourTools
    from media_hygiene.scan.models import MediaFile
    from media_hygiene.scan.stopwatch import Stopwatch


@dataclass(frozen=True, slots=True)
class NearTools:
    """What checking near duplicates needs: colour tools, the index, the stopwatch."""

    colour: ColourTools
    store: MeasureStore
    stopwatch: Stopwatch


def checked_similar(
    inputs: SimilarInputs, policy: KeepPolicy, tools: NearTools
) -> SimilarFindings:
    """Find near duplicates and re-encoded videos, colours and streams checked.

    Each group then says whether it is sure or to check (`near_levels`).

    Args:
        inputs: Files, visual facts, video fingerprints and exact-duplicate groups.
        policy: Protected folders and the usual keep rules.
        tools: `ffmpeg`, the progress sink and the pool to measure colours; the index
            that keeps them; the stopwatch.

    Returns:
        The findings.
    """
    watch = tools.stopwatch
    with watch.timing(Stage.SIMILAR):
        first = find_similar(inputs, policy)
    images = {file.path: file for file in _members(first.near)}
    videos = {file.path: file for file in _members(first.videos)}
    if not images and not videos:
        return with_levels(first)
    with watch.timing(Stage.COLOURS):
        measured = _colours(images, videos, (first, tools))
    visuals = {
        path: replace(visual, colour=measured.get(path))
        for path, visual in inputs.visuals.items()
    }
    looks = {
        path: replace(look, colour=measured.get(path))
        for path, look in inputs.videos.items()
    }
    coloured = replace(
        inputs, visuals=MappingProxyType(visuals), videos=MappingProxyType(looks)
    )
    with watch.timing(Stage.SIMILAR):
        second = find_similar(coloured, policy)
    with watch.timing(Stage.STREAMS):
        return with_levels(same_streams(second, policy, tools.store))


def _colours(
    images: Mapping[Path, MediaFile],
    videos: Mapping[Path, MediaFile],
    context: tuple[SimilarFindings, NearTools],
) -> dict[Path, float]:
    """The colourfulness of the candidates: kept by the index, or measured and kept.

    Args:
        images: The photos found alike, by path.
        videos: The videos found alike, by path.
        context: The first findings (video lengths) and the tools.

    Returns:
        The colourfulness of each candidate known, by path.
    """
    first, tools = context
    candidates = (*images.values(), *videos.values())
    known = tools.store.known(candidates, Measure.COLOUR, float)
    lengths = {
        path: first.video_looks[path].duration for path in videos if path not in known
    }
    missing = [path for path in images if path not in known]
    if not missing and not lengths:
        return known
    measured = asyncio.run(colours(missing, lengths, tools.colour))
    tools.store.keep(candidates, Measure.COLOUR, measured)
    return known | measured


def _members(decisions: Iterable[NearDecision]) -> Iterable[MediaFile]:
    """Every version of every group, kept or not.

    Args:
        decisions: The groups.

    Yields:
        The versions.
    """
    for decision in decisions:
        yield decision.keeper
        yield from decision.removable
        yield from decision.protected
