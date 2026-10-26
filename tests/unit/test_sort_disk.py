"""Sorting progress read from the paths alone (0405): sorted, nothing special, left."""

from __future__ import annotations

from pathlib import Path

import pytest

from media_hygiene.classify.convention import Place, shape_in
from media_hygiene.services.sort_disk import count_paths


@pytest.mark.parametrize(
    ("path", "place"),
    [
        ("/data/c/Photos/2009/2009-11/Anniversaire de Tom/a.jpg", Place.EVENT),
        ("/data/d/Tri/2019/2019-07/Montenegro/Budva/a.jpg", Place.EVENT),
        ("/data/c/Photos/2009/2009-11/a.jpg", Place.NOTHING_SPECIAL),
        ("/data/c/Photos/1985/1985-00/scan.jpg", Place.NOTHING_SPECIAL),
        ("/data/c/Photos/2009/2010-01/a.jpg", Place.LEFT),  # a month of another year
        ("/data/c/Photos/Novembre 2009/a.jpg", Place.LEFT),
        ("/data/c/Photos/2009/a.jpg", Place.LEFT),
        ("/data/c/Photos Chloé/a.jpg", Place.LEFT),
    ],
)
def test_the_shape_is_read_anywhere_in_the_path(path: str, place: Place) -> None:
    """No root to know: the first year folder followed by its month decides."""
    assert shape_in(Path(path).parent.parts).place is place


def test_counts_with_kept_folders_apart_and_the_folders_left() -> None:
    """Protected files never count as left; folders left, the largest first."""
    paths = [
        "/data/c/Photos/2009/2009-11/Tom/1.jpg",
        "/data/c/Photos/2009/2009-11/Tom/2.jpg",
        "/data/c/Photos/2009/2009-11/3.jpg",
        "/data/c/Photos/Divers/4.jpg",
        "/data/c/Photos/Divers/5.jpg",
        "/data/c/Photos/Prints jan10/6.jpg",
        "/data/c/Albums/7.jpg",
    ]
    counted = count_paths(paths, (Path("/data/c/Albums"),))
    assert (counted.sorted, counted.nothing_special, counted.left, counted.kept) == (
        2,
        1,
        3,
        1,
    )
    assert counted.total == 6
    assert counted.folders == (
        ("/data/c/Photos/Divers", 2),
        ("/data/c/Photos/Prints jan10", 1),
    )
