"""The remote's tiles open the shared large view, who is on them included (0830)."""

from __future__ import annotations

from pathlib import Path

from media_hygiene.slideshow.desk import Changes, Desk
from media_hygiene.slideshow.pictures import slides_view
from media_hygiene.slideshow.screens import Screens
from media_hygiene.slideshow.show import Show
from media_hygiene.slideshow.slides import Slide, Timing
from tests.support.page_render import render_page

_TEMPLATES = Path(__file__).resolve().parents[2] / "src" / "media_hygiene"


def test_the_remote_carries_the_shared_large_view_with_its_faces() -> None:
    """Same view, who line and namer as /library: from the shared templates, once."""
    page = render_page("slideshow.html.j2")
    for part in ('id="viewerWho"', "function showWho(", "function whoNamer("):
        assert page.count(part) == 1, part
    assert page.count('id="sizes"') == 1
    assert "showLarge(" in page
    own = (_TEMPLATES / "slideshow" / "templates").glob("*.j2")
    assert not any("function whoFace(" in each.read_text("utf-8") for each in own)


def test_each_slide_gives_the_view_its_file_and_picture() -> None:
    """The path asks who is on it; a photo's TV picture shows it large."""
    slide = Slide(7, "2026-01-02", path="/data/c/Photos/a.jpg")
    desk = Desk(Show((slide,), Timing(8.0)), Screens(), Changes())
    view = slides_view(desk)["slides"]
    assert isinstance(view, list)
    assert view[0]["path"] == "/data/c/Photos/a.jpg"
    assert view[0]["photo"].startswith("tv/7")
