"""Re-encoded videos in the report: the version kept and its copies, with details.

No preview: a video is described by what tells the copies apart, its resolution, its
length, its codec and its size.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.paths.file_uri import file_uri
from media_hygiene.report.gain_order import gain_order
from media_hygiene.report.near_reasons import group_note

if TYPE_CHECKING:
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.plan.similar_models import NearDecision, SimilarFindings
    from media_hygiene.report.near_reasons import GroupNote
    from media_hygiene.scan.models import MediaFile


@dataclass(frozen=True, slots=True)
class VideoView:  # pylint: disable=too-many-instance-attributes
    """One video: where it is, and what tells it from the other versions."""

    path: str
    width: int
    height: int
    duration: float
    codec: str
    size: int
    recorded_at: str | None
    uri: str | None = None  # plays the video itself, when its host path is known
    same_stream: bool = False  # the very picture and sound of the kept video


@dataclass(frozen=True, slots=True)
class VideoNearView:
    """A group of re-encoded videos: the version kept, and its copies."""

    kept: VideoView
    copies: tuple[VideoView, ...]
    protected: tuple[VideoView, ...]
    note: GroupNote  # why, how sure, the space freed (`near_reasons`)


@dataclass(frozen=True, slots=True)
class VideoSection:
    """Every re-encoded video group: `clean --tier near-all` moves them all."""

    groups: tuple[VideoNearView, ...] = ()


def video_section(similar: SimilarFindings, mapper: HostPathMapper) -> VideoSection:
    """Describe the re-encoded videos shown in the report.

    Args:
        similar: The findings, holding the video decisions and their looks.
        mapper: Turns container paths into host paths.

    Returns:
        The section.
    """
    return VideoSection(
        groups=tuple(
            _group(decision, similar, (mapper, share))
            for decision, share in gain_order(similar.videos)
        )
    )


def _group(
    decision: NearDecision,
    similar: SimilarFindings,
    place: tuple[HostPathMapper, int],
) -> VideoNearView:
    """Describe one group.

    Args:
        decision: The video kept and its copies.
        similar: The findings, holding what each video looks like.
        place: Turns container paths into host paths; and the share of the space
            freed by the group and those shown above it.

    Returns:
        Its view.
    """
    mapper, running = place

    def view(file: MediaFile) -> VideoView:
        """Describe one video of the group.

        Args:
            file: The video.

        Returns:
            Its view, in host paths.
        """
        look, path = similar.video_looks[file.path], mapper.to_host(file.path)
        return VideoView(
            path=path,
            width=look.width,
            height=look.height,
            duration=look.duration,
            codec=look.codec or "",
            size=file.size,
            recorded_at=look.recorded_at,
            uri=file_uri(path),
            same_stream=file.path in decision.same_stream,
        )

    return VideoNearView(
        kept=view(decision.keeper),
        copies=tuple(view(file) for file in decision.removable),
        protected=tuple(view(file) for file in decision.protected),
        note=group_note(
            decision, lambda file: similar.video_looks[file.path].pixels, running
        ),
    )
