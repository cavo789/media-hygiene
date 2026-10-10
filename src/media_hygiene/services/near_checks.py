"""Find near duplicates, then check what the hashes cannot see: colours, same streams.

Perceptual hashes are computed in grey. The pictures and videos they find alike are
measured for colour, and the search runs again with it: a black and white edit then
stays apart from its colour original. Measuring only the candidates keeps an audit
light; nothing is stored, so a later audit measures them again.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from types import MappingProxyType
from typing import TYPE_CHECKING

from media_hygiene.plan.similar import SimilarInputs, find_similar
from media_hygiene.scan.colour import ColourTools, colours
from media_hygiene.services.same_streams import same_streams

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.plan.keeper import KeepPolicy
    from media_hygiene.plan.similar_models import NearDecision, SimilarFindings
    from media_hygiene.scan.models import MediaFile


def checked_similar(
    inputs: SimilarInputs, policy: KeepPolicy, tools: ColourTools
) -> SimilarFindings:
    """Find near duplicates and re-encoded videos, colours and streams checked.

    Args:
        inputs: Files, visual facts, video fingerprints and exact-duplicate groups.
        policy: Protected folders and the usual keep rules.
        tools: `ffmpeg` and the progress sink, to measure colours.

    Returns:
        The findings.
    """
    first = find_similar(inputs, policy)
    images = {file.path for file in _members(first.near)}
    videos = {
        file.path: first.video_looks[file.path].duration
        for file in _members(first.videos)
    }
    if not images and not videos:
        return first
    measured = asyncio.run(colours(images, videos, tools))
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
    return same_streams(find_similar(coloured, policy), policy)


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
