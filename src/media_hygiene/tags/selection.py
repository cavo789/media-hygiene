"""Which photos the model sees: one per set of identical files and per burst series.

Identical copies share their tags; the shots of a burst series (`plan.bursts`) take
those of the sharpest one. A video is seen by one frame (`scan.video_still`), when
`ffmpeg` is there and the probe read its length and size. Photos and videos smaller
than `min_edge` are never sent (the model invents details on thumbnails). The newest
photos come first, so that a first night is already useful; videos come last.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import MediaKind
from media_hygiene.plan.bursts import burst_series
from media_hygiene.scan.filters import media_kind
from media_hygiene.scan.models import MediaFile
from media_hygiene.scan.video_still import shown_size

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput

STILLS: Final = frozenset({MediaKind.IMAGE, MediaKind.RAW})
# The kinds seen when `ffmpeg` can take a frame of the videos.
WITH_VIDEOS: Final = STILLS | {MediaKind.VIDEO}


@dataclass(frozen=True, slots=True)
class VisionPlan:
    """The photos to ask about, newest first, and whose answer each photo takes."""

    asked: tuple[MediaInput, ...]
    answered_by: Mapping[Path, Path]  # every photo seen → the photo asked about


def vision_plan(
    files: Sequence[MediaInput],
    min_edge: int,
    kinds: frozenset[MediaKind] = STILLS,
) -> VisionPlan:
    """Choose the photos to describe.

    Args:
        files: The files of the run.
        min_edge: The shorter side below which a photo is never sent, in pixels.
        kinds: The kinds of files seen: photos, and videos when `ffmpeg` is there.

    Returns:
        The photos to ask about, and the photo each eligible one takes its tags from.
    """
    seen = [file for file in files if _eligible(file, min_edge, kinds)]
    copies: dict[str, list[MediaInput]] = {}
    for file in seen:
        copies.setdefault(file.digest or str(file.path), []).append(file)
    firsts = {
        key: min(group, key=lambda file: str(file.path))
        for key, group in copies.items()
    }
    by_path = {file.path: file for file in firsts.values()}
    leader = {path: path for path in by_path}
    shots = [
        MediaFile(file.path, file.size, file.mtime_ns, MediaKind.IMAGE)
        for file in by_path.values()
        if media_kind(file.path) in STILLS
    ]
    visuals = {file.path: file.visual for file in by_path.values() if file.visual}
    for series in burst_series(shots, visuals):
        for shot in series.shots:
            leader[shot.path] = series.best.path
    answered_by = {
        file.path: leader[firsts[key].path]
        for key, group in copies.items()
        for file in group
    }
    asked = sorted(
        (by_path[path] for path in dict.fromkeys(leader.values())),
        key=lambda file: (file.taken_at or "", str(file.path)),
        reverse=True,
    )
    return VisionPlan(tuple(asked), answered_by)


def _eligible(file: MediaInput, min_edge: int, kinds: frozenset[MediaKind]) -> bool:
    """Tell whether the model may see a photo or a video.

    Args:
        file: The file.
        min_edge: The smallest shorter side, in pixels.
        kinds: The kinds of files seen.

    Returns:
        True for a decoded still image large enough, or a video large enough
        whose length is known.
    """
    kind = media_kind(file.path)
    if kind not in kinds:
        return False
    if kind is MediaKind.VIDEO:
        meta = file.metadata
        return meta is not None and bool(meta.duration) and shown_size(meta) >= min_edge
    if file.visual is None:
        return False
    return min(file.visual.width, file.visual.height) >= min_edge
