"""Count what the photos and videos say about themselves, from facts already collected.

No file is read again: the counts come from the checks the audit has just run, or from
the index. RAW files are left out: their metadata is not read.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from media_hygiene.constants import MediaKind

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.scan.broken import IntegrityFindings
    from media_hygiene.scan.models import MediaFile


class Inventory(BaseModel):
    """How many photos and videos of an audit say when and where they were taken."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    images: int = 0
    videos: int = 0
    dated_images: int = 0
    dated_videos: int = 0
    located: int = 0
    formats: dict[str, int] = {}
    video_seconds: float = 0.0


def take_inventory(
    files: Sequence[MediaFile], integrity: IntegrityFindings
) -> Inventory:
    """Count the images and videos, and what their metadata holds.

    Args:
        files: Every media file of the audit.
        integrity: What checking them learnt.

    Returns:
        The counts.
    """
    visuals, metadata = integrity.visuals, integrity.metadata
    images = [file.path for file in files if file.kind is MediaKind.IMAGE]
    videos = [file.path for file in files if file.kind is MediaKind.VIDEO]
    image_facts = [facts for path in images if (facts := metadata.get(path))]
    video_facts = [facts for path in videos if (facts := metadata.get(path))]
    formats = Counter(facts.file_format for facts in image_facts if facts.file_format)
    return Inventory(
        images=len(images),
        videos=len(videos),
        dated_images=sum(
            1 for path in images if (visual := visuals.get(path)) and visual.taken_at
        ),
        dated_videos=sum(1 for facts in video_facts if facts.recorded_at),
        located=sum(1 for facts in (*image_facts, *video_facts) if facts.located),
        formats=dict(formats.most_common()),
        video_seconds=sum(facts.duration or 0.0 for facts in video_facts),
    )
