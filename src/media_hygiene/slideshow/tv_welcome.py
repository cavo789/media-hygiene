"""The TV's welcome page at the bare address of the plain door (0614).

`http://<PC>:8089/` used to lead a TV to the phone's install steps (home server) or
straight to `/screen` (`mh slideshow`). Now both answer this page: the meerkat and the
family's title, and two large tiles a TV remote drives (arrows, OK): *Slideshow*
opens the screen page, *Install on my phone* the certificate's steps. Offline, no
clock, no animation. The home page's look: its lookout meerkat and its two fonts, the
files of `assets/` at their `/assets/` paths (nothing else of that folder served here).
"""

from __future__ import annotations

from http import HTTPStatus
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.home_assets import ASSETS_PREFIX, MAX_AGE_S, asset_file
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.lan_ca_page import PHONE_STEPS
from media_hygiene.review.lan_card import TV_SCREEN
from media_hygiene.slideshow.tv_facts import facts_line

if TYPE_CHECKING:
    from pathlib import Path

WELCOME_PATH: Final = "/"
_MEERKAT: Final = f"{ASSETS_PREFIX}images/meerkat-lookout.webp"
_DISPLAY_FONT: Final = (
    f"{ASSETS_PREFIX}fonts/bricolage-grotesque-latin-opsz-normal.woff2"
)
_TEXT_FONT: Final = f"{ASSETS_PREFIX}fonts/source-sans-3-latin-wght-normal.woff2"
_FILES: Final = MappingProxyType(
    {
        _MEERKAT: ContentType.WEBP,
        _DISPLAY_FONT: ContentType.WOFF2,
        _TEXT_FONT: ContentType.WOFF2,
    }
)
WELCOME_PATHS: Final = frozenset({WELCOME_PATH, *_FILES})
_PACKAGE: Final = "media_hygiene.slideshow"
_TEMPLATE: Final = "tv_welcome.html.j2"


def welcome(path: str, family_title: str, index_file: Path | None = None) -> Response:
    """The welcome page, or one of its files (the meerkat, a font).

    Args:
        path: One of `WELCOME_PATHS`.
        family_title: `[home] family_title`; empty: the family view's own default.
        index_file: The index, for the line of facts (0758); None: no line.

    Returns:
        The page, or the file; 404 when the image lacks it.
    """
    if path in _FILES:
        found = asset_file(path)
        if found is None:
            return Response(HTTPStatus.NOT_FOUND)
        body = found.read_bytes()
        return Response(HTTPStatus.OK, body, _FILES[path], max_age=MAX_AGE_S)
    template = translated_environment(_PACKAGE, escaped=("html", "j2")).get_template(
        _TEMPLATE
    )
    page = template.render(
        title=family_title or _("Our photos"),
        facts=facts_line(index_file) if index_file is not None else "",
        screen=TV_SCREEN,
        phone=PHONE_STEPS,
        meerkat=_MEERKAT,
        display_font=_DISPLAY_FONT,
        text_font=_TEXT_FONT,
    )
    return Response(HTTPStatus.OK, page.encode(), ContentType.HTML)
