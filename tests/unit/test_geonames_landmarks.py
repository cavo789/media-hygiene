"""The landmarks snapshot built from GeoNames' full dump (0472)."""

from __future__ import annotations

import zipfile
from typing import TYPE_CHECKING

from media_hygiene.geo.distance import Point
from media_hygiene.geo.landmarks import Landmarks, near_cells
from tests.support.geonames.landmarks import ALL_TXT, build_landmarks

if TYPE_CHECKING:
    from pathlib import Path


def _row(name: str, place: tuple[float, float], kind: tuple[str, str]) -> str:
    fields = ["1", name, name, "", str(place[0]), str(place[1]), kind[0], kind[1]]
    return "\t".join([*fields, "BE", "", "", "", "", "", "0", "", "", "", ""]) + "\n"


def test_only_monuments_are_kept_and_read_back(tmp_path: Path) -> None:
    """A castle and a church kept, twice the same once; a town and a bridge left out."""
    rows = (
        _row("Castle", (50.123456, 5.0), ("S", "CSTL")),
        _row("Castle", (50.123456, 5.0), ("S", "CSTL")),
        _row("Church", (50.2, 5.1), ("S", "CH")),
        _row("Bridge", (50.3, 5.2), ("S", "BDG")),
        _row("Town", (50.4, 5.3), ("P", "PPL")),
    )
    archive = tmp_path / "all.zip"
    with zipfile.ZipFile(archive, "w") as opened:
        opened.writestr(ALL_TXT, "".join(rows))
    assert build_landmarks(archive, tmp_path) == 2
    landmarks = Landmarks.load(tmp_path)
    assert landmarks.at(Point(50.1235, 5.0)) == "Castle"
    assert landmarks.at(Point(50.3, 5.2)) == ""


def test_only_the_cells_near_photos_are_loaded(tmp_path: Path) -> None:
    """A landmark near a photo is kept, one on another continent is not (0479)."""
    rows = (
        _row("Castle", (50.123456, 5.0), ("S", "CSTL")),
        _row("Pyramid", (29.9792, 31.1342), ("S", "PYR")),
    )
    archive = tmp_path / "all.zip"
    with zipfile.ZipFile(archive, "w") as opened:
        opened.writestr(ALL_TXT, "".join(rows))
    build_landmarks(archive, tmp_path)
    landmarks = Landmarks.load(tmp_path, near_cells([Point(50.9, 5.9)]))
    assert len(landmarks) == 1
    assert landmarks.at(Point(50.1235, 5.0)) == "Castle"
    assert len(Landmarks.load(tmp_path, near_cells([]))) == 0
