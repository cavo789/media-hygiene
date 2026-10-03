"""Re-encoded videos: one video saved again at another size, bit rate or codec.

Two videos are alike when every test agrees: the same length (within half a second or
1 %), the same proportions (±1 %), and the frames at the same moments hash alike: at
most one informative frame may differ (a cut falling between two frame timings), and
at least `MIN_FRAMES` must agree. Frames black or blank in both are not informative.
A copy is kept apart from its original only when it was recorded at the same moment
or has lost its date, as for images: two takes of a still scene stay two videos.

Candidates meet by length: sorted by duration, a video is only compared with the
following ones of about the same length. Video libraries hold thousands of files,
not hundreds of thousands: no hash index is needed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.plan.likeness import distance, is_flat, same_aspect
from media_hygiene.plan.similar_models import NearDecision
from media_hygiene.plan.union_find import UnionFind

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.plan.keeper import KeepPolicy
    from media_hygiene.scan.models import MediaFile
    from media_hygiene.scan.video_models import FrameHash, VideoLook

# Re-encoding blurs a frame more than resizing a photo does; unrelated frames differ
# by about 32 bits.
VIDEO_DISTANCE: Final = 10
MIN_FRAMES: Final = 3
_DURATION_SECONDS: Final = 0.5
_DURATION_SHARE: Final = 0.01
# Dates as written: compared to the second (a copy may lose the fraction).
_DATE_LENGTH: Final = 19


def alike(first: VideoLook, second: VideoLook) -> bool:
    """Tell whether two videos show the same thing (date aside).

    Args:
        first: A video.
        second: Another video.

    Returns:
        True when the length, the proportions and the frames agree.
    """
    return (
        _same_length(first.duration, second.duration)
        and same_aspect((first.width, first.height), (second.width, second.height))
        and _frames_agree(first.print.frames, second.print.frames)
    )


def is_near_video(best: VideoLook, other: VideoLook) -> bool:
    """Tell whether `other` is a re-encoded copy of `best`.

    Args:
        best: The version kept.
        other: The candidate copy.

    Returns:
        True when they are alike and the copy has the same date or none.
    """
    date = other.recorded_at
    return alike(best, other) and (
        date is None
        or (
            best.recorded_at is not None
            and date[:_DATE_LENGTH] == best.recorded_at[:_DATE_LENGTH]
        )
    )


def video_near_decisions(
    files: Sequence[MediaFile],
    looks: Mapping[Path, VideoLook],
    policy: KeepPolicy,
) -> tuple[NearDecision, ...]:
    """Group re-encoded videos and choose the version to keep in each group.

    The highest resolution is kept, then the largest file (the highest bit rate),
    then the usual keep rules. Protected copies are never removable.

    Args:
        files: Candidate videos, one per exact-duplicate group.
        looks: What each video looks like.
        policy: Protected folders and the usual keep rules.

    Returns:
        The decisions, the largest keeper first.
    """
    usable = sorted(
        (file for file in files if file.path in looks),
        key=lambda file: looks[file.path].duration,
    )
    decisions: list[NearDecision] = []
    for cluster in _clusters(usable, looks):
        keeper = min(
            cluster,
            key=lambda file: (-looks[file.path].pixels, -file.size, policy.rank(file)),
        )
        best = looks[keeper.path]
        near = [
            file
            for file in cluster
            if file != keeper and is_near_video(best, looks[file.path])
        ]
        removable = tuple(file for file in near if not policy.is_protected(file))
        if removable:
            protected = tuple(file for file in near if policy.is_protected(file))
            decisions.append(NearDecision(keeper, removable, protected))
    return tuple(sorted(decisions, key=lambda d: (-d.keeper.size, str(d.keeper.path))))


def _clusters(
    files: Sequence[MediaFile], looks: Mapping[Path, VideoLook]
) -> Iterable[list[MediaFile]]:
    """Link alike videos of about the same length, and return the linked sets.

    Args:
        files: Candidate videos, sorted by duration.
        looks: What each video looks like.

    Returns:
        The sets of two videos or more.
    """
    links = UnionFind(files)
    for first, file in enumerate(files):
        look = looks[file.path]
        for second in range(first + 1, len(files)):
            other = looks[files[second].path]
            if not _same_length(look.duration, other.duration):
                break
            if alike(look, other):
                links.link(first, second)
    return links.sets()


def _same_length(first: float, second: float) -> bool:
    """Tell whether two lengths agree, within half a second or 1 %.

    Args:
        first: A duration in seconds.
        second: Another duration.

    Returns:
        True when close enough for a re-encoded copy.
    """
    tolerance = max(_DURATION_SECONDS, _DURATION_SHARE * max(first, second))
    return abs(first - second) <= tolerance


def _frames_agree(first: Sequence[FrameHash], second: Sequence[FrameHash]) -> bool:
    """Tell whether the frames of two videos, moment by moment, hash alike.

    Args:
        first: The frame hashes of one video.
        second: Those of the other, at the same moments.

    Returns:
        True when at most one informative frame differs and enough agree.
    """
    informative = [
        (one, two)
        for one, two in zip(first, second, strict=True)
        if not (is_flat(one.dhash) and is_flat(two.dhash))
    ]
    agreeing = sum(
        distance(one.dhash, two.dhash) <= VIDEO_DISTANCE
        and distance(one.phash, two.phash) <= VIDEO_DISTANCE
        for one, two in informative
    )
    return agreeing >= max(MIN_FRAMES, len(informative) - 1)
