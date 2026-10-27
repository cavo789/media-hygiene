"""0373: a video found by the search is played in the large view, not as a JPEG."""

from __future__ import annotations

from pathlib import Path

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.search.models import Found, Hit
from media_hygiene.search.views import found_view


def _hits(*names: str) -> list[dict[str, object]]:
    """The page's view of files found.

    Args:
        *names: Their names, below `/data/c`.

    Returns:
        One JSON object per file.
    """
    hits = tuple(
        Hit(key, PhotoVersion(Path("/data/c") / name, 1, 1), "2015-07-28", {})
        for key, name in enumerate(names)
    )
    view = found_view(Found(len(hits), hits), HostPathMapper(Path("/data")))
    return view["hits"]  # type: ignore[return-value]


def test_a_video_carries_its_address_and_a_frame() -> None:
    """A `.MOV` gets `/video/…`, and its thumbnail (one frame); a photo no video."""
    movie, photo = _hits("IMG_1775.MOV", "IMG_1.jpg")
    assert movie["video"] == "/video/0.mov"
    assert movie["thumb"] == "/thumb/0.jpg"
    assert photo["video"] == ""
