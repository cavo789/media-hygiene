"""Every page served wears the home page's look (0268, 0271, 0272).

One theme (`theme.css.j2`) and one bar (`page_header.html.j2`) for the eleven pages:
the name, the page's name, its chapter of the documentation in both languages, and
"Back to the home page" only when `mh` opened the page from the home page. Their
fonts and images come from `/assets/`, served by the door every page shares.
"""

from __future__ import annotations

import asyncio
import re
from http import HTTPStatus
from pathlib import Path
from typing import Final

import pytest

from media_hygiene.constants import DOC_PAGES, Locale
from media_hygiene.i18n import using
from media_hygiene.places.app import PAGE_POLICY
from media_hygiene.review.ending import Ending, EndingDoor
from media_hygiene.review.http import ContentType, Request, Response
from media_hygiene.review.page_header import PAGE_STEPS, page_header
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from tests.support.page_render import FRAME_EXTENDS, render_page
from tests.unit.test_documentation import DOCUMENTATION, anchors

_SRC: Final = Path(__file__).resolve().parents[2] / "src" / "media_hygiene"
_LINK: Final = re.compile(r'<a class="mh-doc" href="(?P<url>[^"]+)"')


def _chapter(url: str) -> tuple[Path, str]:
    """The documentation file and the anchor a link of the site names."""
    page, _hash, anchor = url.removeprefix(f"{DOC_PAGES}/").partition("#")
    locale = Locale.FR.value if page.startswith("fr/") else Locale.EN.value
    page = page.removeprefix("fr/").rstrip("/")
    return (DOCUMENTATION / locale / page).with_suffix(".md"), anchor


@pytest.fixture
def from_home(monkeypatch: pytest.MonkeyPatch) -> None:
    """`mh` opened the page from the home page."""
    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, "1")


@pytest.mark.parametrize("locale", list(Locale))
@pytest.mark.parametrize("template", sorted(PAGE_STEPS))
def test_each_page_shows_its_bar_and_its_chapter(
    template: str, locale: Locale, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The bar, and its two doc links: the page's chapter, in both languages."""
    monkeypatch.delenv(LAUNCHER_STEPS_VARIABLE, raising=False)
    with using(locale):
        page = render_page(template)
    assert page.count('class="mh-bar"') == 1
    assert "Media Hygiene" in page
    assert 'id="homeLink"' not in page
    links = _LINK.findall(page)
    assert len(links) == 2
    for file, anchor in map(_chapter, links):
        assert file.is_file(), file
        assert not anchor or anchor in anchors(file), (file, anchor)
    assert ("/fr/" in links[0]) is (locale is Locale.FR)
    assert ("/fr/" in links[1]) is (locale is Locale.EN)


@pytest.mark.parametrize("template", sorted(PAGE_STEPS))
def test_each_page_has_one_h1_and_it_is_the_bars(template: str) -> None:
    """0282: the board's own title is gone; the bar's page name is the page's `<h1>`."""
    page = render_page(template)
    headings = re.findall(r"<h1\b[^>]*>(.*?)</h1>", page, re.DOTALL)
    assert len(headings) == 1
    assert '<h1 class="mh-page">' in page
    assert f"<title>{headings[0]} \u2014 media-hygiene</title>" in page


@pytest.mark.parametrize("template", sorted(PAGE_STEPS))
def test_each_page_wears_the_theme(template: str) -> None:
    """The theme's tokens and fonts, no colours of its own any more."""
    page = render_page(template)
    assert "--mk-bg:" in page
    assert page.count("/assets/fonts/") == 4
    assert "mh-home-theme" in page  # the switch of the home page is read
    assert "--bg: #" not in page


@pytest.mark.usefixtures("from_home")
@pytest.mark.parametrize("template", sorted(PAGE_STEPS))
def test_opened_from_home_the_page_offers_the_way_back(template: str) -> None:
    """The way back, handled by the fragment every page includes."""
    page = render_page(template)
    assert page.count('id="homeLink"') == 1
    assert 'getElementById("homeLink")' in page
    # 0280: back on the section of the home page this tab was left from.
    assert 'sessionStorage.getItem("mh-home-section")' in page
    assert 'window.location.replace("/" + section());' in page


@pytest.mark.usefixtures("from_home")
def test_the_phone_page_offers_the_way_back_and_says_nothing_is_deleted() -> None:
    """0332: the same link at the same place; it ends the page as Leave everything."""
    assert page_header("phone_review.html.j2").home
    page = render_page("phone_review.html.j2")
    assert "nothing is deleted from the phone" in page.split('id="homeLink"')[1]
    assert "window.mhAwaitHome = awaitHome;" in page


def test_from_the_console_the_phone_page_has_no_way_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`import --phone --free` typed: no home page to go back to, as elsewhere."""
    monkeypatch.delenv(LAUNCHER_STEPS_VARIABLE, raising=False)
    assert not page_header("phone_review.html.j2").home
    assert 'id="homeLink"' not in render_page("phone_review.html.j2")


class _Refusing:
    """A page that answers nothing itself."""

    async def handle(self, request: Request) -> Response:
        """Refuse every request.

        Args:
            request: The request.

        Returns:
            403.
        """
        del request
        return Response(HTTPStatus.FORBIDDEN)


def _get(path: str, host: str = "127.0.0.1") -> Response:
    door = EndingDoor(_Refusing(), Ending())
    return asyncio.run(door.handle(Request("GET", path, {"host": host})))


def test_the_door_of_every_page_serves_the_assets() -> None:
    """Fonts and the avatar for any page; `../` refused; other hosts: the page's."""
    font = _get("/assets/fonts/source-sans-3-latin-wght-normal.woff2")
    assert font.status == HTTPStatus.OK
    assert font.content_type is ContentType.WOFF2
    assert _get("/assets/images/avatar.webp").content_type is ContentType.WEBP
    assert _get("/assets/../review/http.py").status == HTTPStatus.NOT_FOUND
    assert _get("/assets/%2e%2e/review/http.py").status == HTTPStatus.NOT_FOUND
    other = _get("/assets/images/avatar.webp", "example.com")
    assert other.status == HTTPStatus.FORBIDDEN


def test_the_places_policy_lets_the_fonts_in_and_names_the_tiles_only() -> None:
    """`font-src 'self'`, and the tile server the only outside host."""
    policy = PAGE_POLICY.format(tiles="https://tile.example.org")
    assert "font-src 'self'" in policy
    assert re.findall(r"https?://[^\s;]+", policy) == ["https://tile.example.org"]


def test_every_page_template_includes_the_theme_and_the_bar() -> None:
    """The seventeen pages, from their templates: the frame's parts, or their own."""
    pages = [
        path for path in _SRC.glob("*/templates/*.html.j2") if path.name in PAGE_STEPS
    ]
    assert len(pages) == len(PAGE_STEPS) == 17
    for path in pages:
        text = path.read_text("utf-8")
        framed = text.startswith(FRAME_EXTENDS)
        assert framed or 'include "theme.css.j2"' in text, path.name
        assert framed or 'include "page_header.html.j2"' in text, path.name


def test_every_door_answers_the_favicon_browsers_ask_for() -> None:
    """`/favicon.ico` is the meerkat (0278), 200 on the loopback, refused elsewhere."""
    icon = _get("/favicon.ico")
    assert icon.status == HTTPStatus.OK
    assert icon.content_type is ContentType.PNG
    assert _get("/assets/images/favicon.png").body == icon.body
    assert _get("/favicon.ico", host="evil.example").status == HTTPStatus.FORBIDDEN


def test_every_served_page_declares_the_favicon_its_policy_allows() -> None:
    """Each served page links the icon; places allows images of `self`."""
    link = 'rel="icon" type="image/png" href="/assets/images/favicon.png"'
    missing = [page for page in sorted(PAGE_STEPS) if link not in render_page(page)]
    assert missing == []
    shells = (
        _SRC / "review" / "templates" / "home.html.j2",
        _SRC / "docs" / "templates" / "doc.html.j2",
    )
    assert [
        shell.name for shell in shells if link not in shell.read_text("utf-8")
    ] == []
    assert "img-src 'self'" in PAGE_POLICY
