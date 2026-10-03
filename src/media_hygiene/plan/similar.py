"""Find pictures that look alike: burst series, near duplicates, re-encoded videos.

Each exact-duplicate group takes part once, through the copy it keeps: its other copies
are already handled by the exact tier. Burst shots never count as near duplicates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING

from media_hygiene.plan.bursts import burst_series
from media_hygiene.plan.near import near_decisions
from media_hygiene.plan.near_video import video_near_decisions
from media_hygiene.plan.similar_models import SimilarFindings

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from media_hygiene.plan.keeper import KeepPolicy
    from media_hygiene.scan.models import DuplicateGroup, MediaFile, VisualFacts
    from media_hygiene.scan.video_models import VideoLook


@dataclass(frozen=True, slots=True)
class SimilarInputs:
    """What the audit knows: the files, what images and videos look like, the groups."""

    files: Sequence[MediaFile]
    visuals: Mapping[Path, VisualFacts]
    groups: Sequence[DuplicateGroup]
    videos: Mapping[Path, VideoLook] = field(
        default_factory=lambda: MappingProxyType({})
    )


def find_similar(inputs: SimilarInputs, policy: KeepPolicy) -> SimilarFindings:
    """List burst series and near duplicates of images, and re-encoded videos.

    Args:
        inputs: Files, visual facts, video fingerprints and exact-duplicate groups.
        policy: Protected folders and the usual keep rules.

    Returns:
        The findings, with the visual facts for the report.
    """
    other_copies = {
        file.path
        for decision in (policy.decide(group) for group in inputs.groups)
        for file in (*decision.removable, *decision.protected)
    }
    candidates = [
        file
        for file in inputs.files
        if file.path in inputs.visuals and file.path not in other_copies
    ]
    videos = video_near_decisions(
        [file for file in inputs.files if file.path not in other_copies],
        inputs.videos,
        policy,
    )
    bursts = burst_series(candidates, inputs.visuals)
    in_bursts = {file.path for series in bursts for file in series.shots}
    near = near_decisions(
        [file for file in candidates if file.path not in in_bursts],
        inputs.visuals,
        policy,
    )
    return SimilarFindings(
        near=near,
        bursts=bursts,
        visuals=inputs.visuals,
        videos=videos,
        video_looks=inputs.videos,
    )
