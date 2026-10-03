"""Re-encoded videos in the report: the version kept and its copies, with details.

No preview: a video is described by what tells the copies apart, its resolution, its
length, its codec and its size.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.constants import Sizes

if TYPE_CHECKING:
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.plan.similar_models import NearDecision, SimilarFindings
    from media_hygiene.scan.models import MediaFile


@dataclass(frozen=True, slots=True)
class VideoView:
    """One video: where it is, and what tells it from the other versions."""

    path: str
    width: int
    height: int
    duration: float
    codec: str
    size: int
    recorded_at: str | None


@dataclass(frozen=True, slots=True)
class VideoNearView:
    """A group of re-encoded videos: the version kept, and its copies."""

    kept: VideoView
    copies: tuple[VideoView, ...]
    protected: tuple[VideoView, ...]


@dataclass(frozen=True, slots=True)
class VideoSection:
    """The groups shown, and how many are left out."""

    groups: tuple[VideoNearView, ...] = ()
    hidden: int = 0


def video_section(similar: SimilarFindings, mapper: HostPathMapper) -> VideoSection:
    """Describe the re-encoded videos shown in the report.

    Args:
        similar: The findings, holding the video decisions and their looks.
        mapper: Turns container paths into host paths.

    Returns:
        The section.
    """
    limit = Sizes.MAX_SIMILAR_IN_REPORT
    return VideoSection(
        groups=tuple(
            _group(decision, similar, mapper) for decision in similar.videos[:limit]
        ),
        hidden=max(0, len(similar.videos) - limit),
    )


def _group(
    decision: NearDecision, similar: SimilarFindings, mapper: HostPathMapper
) -> VideoNearView:
    """Describe one group.

    Args:
        decision: The video kept and its copies.
        similar: The findings, holding what each video looks like.
        mapper: Turns container paths into host paths.

    Returns:
        Its view.
    """

    def view(file: MediaFile) -> VideoView:
        """Describe one video of the group.

        Args:
            file: The video.

        Returns:
            Its view, in host paths.
        """
        look = similar.video_looks[file.path]
        return VideoView(
            path=mapper.to_host(file.path),
            width=look.width,
            height=look.height,
            duration=look.duration,
            codec=look.codec or "",
            size=file.size,
            recorded_at=look.recorded_at,
        )

    return VideoNearView(
        kept=view(decision.keeper),
        copies=tuple(view(file) for file in decision.removable),
        protected=tuple(view(file) for file in decision.protected),
    )
