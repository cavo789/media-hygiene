"""The TV's welcome page at the bare address of the plain door (0614).

`http://<PC>:8089/` used to lead a TV to the phone's install steps (home server) or
straight to `/screen` (`mh slideshow`). Now both answer this page: the meerkat and the
family's title, and two large tiles a TV remote drives (arrows, OK): *This is the TV*
opens the screen page, *Install on my phone* the certificate's steps. Offline, no
clock, no animation. The meerkat is the app's own icon (`app_shell.icon`), served at
the same path as on the HTTPS door.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Final

from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.app_shell import ICON_PATH, icon
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.lan_ca_page import PHONE_STEPS
from media_hygiene.review.lan_card import TV_SCREEN

WELCOME_PATH: Final = "/"
_ICON_SIZE: Final = 192  # one of the app's icon sizes: no new picture
WELCOME_ICON: Final = ICON_PATH.format(size=_ICON_SIZE)
WELCOME_PATHS: Final = frozenset({WELCOME_PATH, WELCOME_ICON})
_PACKAGE: Final = "media_hygiene.slideshow"
_TEMPLATE: Final = "tv_welcome.html.j2"


def welcome(path: str, family_title: str) -> Response:
    """The welcome page, or its meerkat.

    Args:
        path: One of `WELCOME_PATHS`.
        family_title: `[home] family_title`; empty: the family view's own default.

    Returns:
        The page, or the meerkat as PNG.
    """
    if path == WELCOME_ICON:
        return Response(HTTPStatus.OK, icon(_ICON_SIZE), ContentType.PNG)
    template = translated_environment(_PACKAGE, escaped=("html", "j2")).get_template(
        _TEMPLATE
    )
    page = template.render(
        title=family_title or _("Our photos"),
        screen=TV_SCREEN,
        phone=PHONE_STEPS,
        meerkat=WELCOME_ICON,
    )
    return Response(HTTPStatus.OK, page.encode(), ContentType.HTML)
