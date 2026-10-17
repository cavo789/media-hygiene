"""The photos most likely unwanted: each reason, its threshold, the exclusions."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from media_hygiene.config.review_settings import UnwantedSettings
from media_hygiene.constants import MediaKind
from media_hygiene.plan.unwanted import (
    UnwantedPhoto,
    UnwantedReason,
    UnwantedSource,
    blur_threshold,
    unwanted_photos,
)
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.scan.models import MediaFile, VisualFacts
from media_hygiene.services.unwanted_reviewing import unwanted_limits

SHARP = 500.0
NORMAL = {"brightness": 120.0, "dark_share": 0.01, "bright_share": 0.01}
DARK = {"brightness": 10.0, "dark_share": 0.9, "bright_share": 0.0}
WHITE = {"brightness": 245.0, "dark_share": 0.0, "bright_share": 0.8}


def photo(
    name: str, size: tuple[int, int] = (4000, 3000), sharpness: float = SHARP
) -> tuple[MediaFile, VisualFacts]:
    """A photo and its visual facts."""
    file = MediaFile(Path(f"/data/c/Photos/{name}"), 1000, 1, MediaKind.IMAGE)
    width, height = size
    return file, VisualFacts(0, 0, width, height, sharpness)


def source(
    photos: list[tuple[MediaFile, VisualFacts]],
    exposures: dict[str, dict[str, float]] | None = None,
    excluded: frozenset[Path] = frozenset(),
) -> UnwantedSource:
    """What the audit knows of these photos."""
    metadata = {
        file.path: MediaMetadata.model_validate(
            (exposures or {}).get(file.path.name, NORMAL)
        )
        for file, _visual in photos
    }
    return UnwantedSource(
        [file for file, _visual in photos],
        {file.path: visual for file, visual in photos},
        metadata,
        excluded,
    )


def reasons(found: tuple[UnwantedPhoto, ...]) -> dict[str, str]:
    """Name -> reason of the photos found."""
    return {item.file.path.name: item.reason for item in found}


def never(_file: MediaFile) -> bool:
    """No screenshot."""
    return False


def collection() -> list[tuple[MediaFile, VisualFacts]]:
    """Fifty sharp photos, then a tiny, a dark, a white, a blurred one, a screenshot."""
    photos = [
        photo(f"IMG_{index:03d}.jpg", sharpness=SHARP + index) for index in range(50)
    ]
    photos += [
        photo("icon.jpg", size=(200, 200)),
        photo("night.jpg"),
        photo("snow.jpg"),
        photo("shaken.jpg", sharpness=3.0),
        photo("Screenshot_1.jpg"),
    ]
    return photos


EXPOSURES = {"night.jpg": DARK, "snow.jpg": WHITE}


def screenshot_name(file: MediaFile) -> bool:
    """`classify`'s test, reduced to the name."""
    return file.path.name.startswith("Screenshot")


def test_each_reason_finds_its_photo() -> None:
    """Tiny, screenshot, dark, white, blurriest: one photo each, sharp ones never."""
    limits = unwanted_limits(UnwantedSettings())
    found = unwanted_photos(source(collection(), EXPOSURES), limits, screenshot_name)
    assert reasons(found) == {
        "icon.jpg": UnwantedReason.TINY,
        "night.jpg": UnwantedReason.DARK,
        "snow.jpg": UnwantedReason.WHITE,
        "shaken.jpg": UnwantedReason.BLURRY,
        "Screenshot_1.jpg": UnwantedReason.SCREENSHOT,
    }


@pytest.mark.parametrize(
    ("setting", "gone"),
    [
        ({"tiny_megapixels": 0}, "icon.jpg"),
        ({"screenshots": False}, "Screenshot_1.jpg"),
        ({"dark_mean": 0}, "night.jpg"),
        ({"white_mean": 0}, "snow.jpg"),
        ({"blur_percentile": 0}, "shaken.jpg"),
    ],
)
def test_zero_disables_a_reason(setting: dict[str, object], gone: str) -> None:
    """Each threshold at 0 (or False) leaves its photo out, the others in."""
    limits = unwanted_limits(UnwantedSettings.model_validate(setting))
    found = reasons(
        unwanted_photos(source(collection(), EXPOSURES), limits, screenshot_name)
    )
    assert gone not in found
    assert len(found) == 4


def test_the_thresholds_are_settings() -> None:
    """A larger tiny size, a stricter dark share: the photos follow."""
    photos = [photo("small.jpg", size=(800, 600)), photo("dim.jpg")]
    dim = {"dim.jpg": {"brightness": 20.0, "dark_share": 0.5, "bright_share": 0.0}}
    default = unwanted_limits(UnwantedSettings(blur_percentile=0))
    assert not unwanted_photos(source(photos, dim), default, never)
    wider = unwanted_limits(
        UnwantedSettings(tiny_megapixels=0.5, dark_share=0.4, blur_percentile=0)
    )
    assert reasons(unwanted_photos(source(photos, dim), wider, never)) == {
        "small.jpg": UnwantedReason.TINY,
        "dim.jpg": UnwantedReason.DARK,
    }


def test_the_blur_threshold_follows_the_collection() -> None:
    """A percentile of the collection's own sharpness, as numpy computes it."""
    values = [float(value) for value in range(1, 101)]
    assert blur_threshold(values, 2) == pytest.approx(np.percentile(values, 2))
    assert blur_threshold(values, 0) is None
    assert blur_threshold([], 2) is None
    soft = [photo(f"soft_{index}.jpg", sharpness=10.0 + index) for index in range(50)]
    limits = unwanted_limits(UnwantedSettings())
    found = reasons(unwanted_photos(source(soft), limits, never))
    assert found == {"soft_0.jpg": UnwantedReason.BLURRY}  # 10 < 10.98, the 2 %


def test_excluded_photos_are_never_listed() -> None:
    """Protected, burst shots, near duplicates: the caller names them, never listed."""
    photos = collection()
    excluded = frozenset(file.path for file, _visual in photos[50:])
    limits = unwanted_limits(UnwantedSettings())
    found = unwanted_photos(
        source(photos, EXPOSURES, excluded), limits, screenshot_name
    )
    assert all(item.file.path not in excluded for item in found)


def test_the_largest_reason_comes_first() -> None:
    """Groups ordered by their number of photos, each by path."""
    photos = [photo(f"t{index}.jpg", size=(100, 100)) for index in (2, 1, 3)]
    photos.append(photo("Screenshot_9.jpg"))
    limits = unwanted_limits(UnwantedSettings(blur_percentile=0))
    found = unwanted_photos(source(photos), limits, screenshot_name)
    assert [item.file.path.name for item in found] == [
        "t1.jpg",
        "t2.jpg",
        "t3.jpg",
        "Screenshot_9.jpg",
    ]
