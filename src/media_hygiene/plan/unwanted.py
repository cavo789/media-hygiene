"""The photos most likely unwanted: tiny, screenshots, nearly black or white, blurriest.

Facts only, measured by the audit: the size, `classify`'s screenshot test, the
exposure, the sharpness. The blurriest are those under a percentile of the collection's
own sharpness, so the threshold follows each collection and camera. Nothing here sets
anything aside: `review --junk` shows the photos, the user decides.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

from media_hygiene.scan.exposure import exposure_of

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.scan.metadata import MediaMetadata
    from media_hygiene.scan.models import MediaFile, VisualFacts

_MEGA: Final = 1_000_000
_PERCENT: Final = 100


class UnwantedReason(StrEnum):
    """Why a photo is shown as likely unwanted: one reason per photo, this order."""

    SCREENSHOT = "screenshot"
    TINY = "tiny"
    DARK = "dark"
    WHITE = "white"
    BLURRY = "blurry"


@dataclass(frozen=True, slots=True)
class Flat:
    """A nearly uniform picture: its mean brightness past `mean`, `share` clipped."""

    mean: float  # 0 disables the reason
    share: float


@dataclass(frozen=True, slots=True)
class UnwantedLimits:
    """The thresholds of `[review.unwanted]`; each at 0 disables its reason."""

    tiny_megapixels: float
    screenshots: bool
    dark: Flat
    white: Flat
    blur_percentile: float


@dataclass(frozen=True, slots=True)
class UnwantedSource:
    """The pictures an audit compared, what it knows of them, those never listed."""

    images: Sequence[MediaFile]
    visuals: Mapping[Path, VisualFacts]
    metadata: Mapping[Path, MediaMetadata]
    excluded: frozenset[Path]  # protected, burst shots, near duplicates


@dataclass(frozen=True, slots=True)
class UnwantedPhoto:
    """One photo shown as likely unwanted, and why."""

    file: MediaFile
    reason: UnwantedReason


def blur_threshold(sharpness: Sequence[float], percentile: float) -> float | None:
    """The sharpness under which a photo is among the blurriest of the collection.

    Args:
        sharpness: The sharpness of every photo of the collection.
        percentile: 0 to 100; 0 disables the reason.

    Returns:
        The threshold, or None when disabled or without photos.
    """
    if not percentile or not sharpness:
        return None
    values = sorted(sharpness)  # interpolated between ranks, as numpy's default
    position = (len(values) - 1) * percentile / _PERCENT
    low = int(position)
    high = min(low + 1, len(values) - 1)
    return values[low] + (values[high] - values[low]) * (position - low)


def unwanted_photos(
    source: UnwantedSource,
    limits: UnwantedLimits,
    screenshot: Callable[[MediaFile], bool],
) -> tuple[UnwantedPhoto, ...]:
    """List the photos most likely unwanted, the largest reason first.

    Args:
        source: The pictures, their facts and those never listed.
        limits: The thresholds.
        screenshot: `classify`'s screenshot test.

    Returns:
        The photos, grouped by reason (the reason with the most photos first), each
        group by path.
    """
    visuals = source.visuals
    sharpness = [visuals[file.path].sharpness for file in source.images]
    blur = blur_threshold(sharpness, limits.blur_percentile)
    found: defaultdict[UnwantedReason, list[MediaFile]] = defaultdict(list)
    for file in source.images:
        if file.path in source.excluded:
            continue
        reason = _reason(file, (source, limits), (blur, screenshot))
        if reason is not None:
            found[reason].append(file)
    order = sorted(found, key=lambda reason: (-len(found[reason]), reason))
    return tuple(
        UnwantedPhoto(file, reason)
        for reason in order
        for file in sorted(found[reason], key=lambda file: str(file.path))
    )


def _reason(
    file: MediaFile,
    known: tuple[UnwantedSource, UnwantedLimits],
    tests: tuple[float | None, Callable[[MediaFile], bool]],
) -> UnwantedReason | None:
    """Tell why a photo is likely unwanted, the first reason that holds.

    Args:
        file: The photo.
        known: The audit's facts, and the thresholds.
        tests: The blur threshold of the collection, and the screenshot test.

    Returns:
        The reason, or None.
    """
    source, limits = known
    blur, screenshot = tests
    visual = source.visuals[file.path]
    if limits.screenshots and screenshot(file):
        return UnwantedReason.SCREENSHOT
    if visual.pixels and visual.pixels < limits.tiny_megapixels * _MEGA:
        return UnwantedReason.TINY
    exposure = exposure_of(source.metadata.get(file.path))
    if exposure is not None:
        dark, white = limits.dark, limits.white
        if exposure.brightness < dark.mean and exposure.dark_share >= dark.share:
            return UnwantedReason.DARK
        bright = white.mean and exposure.brightness > white.mean
        if bright and exposure.bright_share >= white.share:
            return UnwantedReason.WHITE
    if blur is not None and visual.sharpness < blur:
        return UnwantedReason.BLURRY
    return None
