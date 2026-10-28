"""The drawer of the `places` map: files grouped by folder, in host paths (0232, 0233).

The largest folder first, each file with its folder as the user knows it; a picture
has two previews, a video none; a file moved since the audit keeps its place.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.constants import MediaKind
from media_hygiene.geo.distance import Point
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.places.drawer_rows import LARGE_PREFIX, Shown, drawer_rows
from media_hygiene.review.views import PREVIEW_PREFIX
from media_hygiene.scan.models import MediaFile

if TYPE_CHECKING:
    from pathlib import Path


def _shown(path: Path, kind: MediaKind = MediaKind.IMAGE) -> Shown:
    """A file of the drawer, written on disk, without a position."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x")
    return Shown(MediaFile(path, 1, 1, kind))


def test_the_largest_folder_comes_first_each_in_its_host_path(tmp_path: Path) -> None:
    r"""Two drives: `C:\Photos\Geer` (two files) before `D:\Trips` (one)."""
    data = tmp_path / "data"
    trip = _shown(data / "d" / "Trips" / "a.jpg")
    geer = [_shown(data / "c" / "Photos" / "Geer" / f"IMG_{n}.jpg") for n in (1, 2)]
    sources: dict[str, Path] = {}

    rows = drawer_rows([trip, *geer], HostPathMapper(data), sources)

    assert [(row["folder"], row["name"]) for row in rows] == [
        ("C:\\Photos\\Geer", "IMG_1.jpg"),
        ("C:\\Photos\\Geer", "IMG_2.jpg"),
        ("D:\\Trips", "a.jpg"),
    ]
    assert sorted(sources.values()) == sorted(item.file.path for item in [trip, *geer])


def test_a_picture_has_two_previews_a_video_none(tmp_path: Path) -> None:
    """The grid's and the viewer's, of one key; a video is listed by its name."""
    folder = tmp_path / "data" / "c" / "Clips"
    picture, video = _shown(folder / "a.jpg"), _shown(folder / "b.mp4", MediaKind.VIDEO)
    sources: dict[str, Path] = {}

    first, second = drawer_rows([picture, video], HostPathMapper(tmp_path), sources)

    preview, large = str(first["preview"]), str(first["large"])
    assert f"/{preview}".startswith(PREVIEW_PREFIX)  # relative to the page (0417)
    assert f"/{large}" == f"/{preview}".replace(PREVIEW_PREFIX, LARGE_PREFIX)
    assert (first["video"], second["video"]) == (False, True)
    assert "preview" not in second
    assert list(sources.values()) == [picture.file.path]


def test_a_file_moved_since_keeps_its_place_and_a_position_is_sent(
    tmp_path: Path,
) -> None:
    """Renamed after the audit: not found, still in its folder, in its order."""
    folder = tmp_path / "data" / "c" / "Photos"
    gone, kept = _shown(folder / "a.jpg"), _shown(folder / "b.jpg")
    gone.file.path.unlink()
    located = Shown(kept.file, Point(50.1, 5.2))

    rows = drawer_rows([gone, located], HostPathMapper(tmp_path / "data"), {})

    assert [(row["name"], row["found"]) for row in rows] == [
        ("a.jpg", False),
        ("b.jpg", True),
    ]
    assert "latitude" not in rows[0]
    assert (rows[1]["latitude"], rows[1]["longitude"]) == (50.1, 5.2)
