"""The bar on top of every page served but the home page (`page_header.html.j2`, 0268).

"Media Hygiene", the avatar and the page's name; its chapter of the documentation in the
page's language and in the other one (the catalog's `doc` of the action that opens the
page); "Back to the home page" only when `mh` opened the page from the home page (it
sets `MEDIA_HYGIENE_LAUNCHER_STEPS` for those runs alone, the phone's page too, 0332):
elsewhere, ending the page would bring nothing back.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.menu_catalog import catalog
from media_hygiene.cli.menu_entry import Doc
from media_hygiene.constants import Locale
from media_hygiene.docs.served import served_url
from media_hygiene.i18n import active_locale
from media_hygiene.review.home_assets import ASSETS_PREFIX
from media_hygiene.review.step_watch import keeps_server
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE

if TYPE_CHECKING:
    from collections.abc import Mapping

    from jinja2 import Environment

# What an album is, what the albums' page does (0349): the chapter of its bar (0342).
ALBUMS_DOC: Final = Doc("reference-albums/")
# Each page's template, and the action of the catalog that opens it: its chapter; or
# the chapter itself, for a page no action opens (the albums, a home page group, 0342).
PAGE_STEPS: Final[Mapping[str, str | Doc]] = MappingProxyType(
    {
        "review.html.j2": "review",
        "near_review.html.j2": "review-near",
        "pairs_review.html.j2": "review-pairs",
        "unwanted_review.html.j2": "review-junk",
        "gone_review.html.j2": "review-gone",
        "intruders_review.html.j2": "review-intruders",
        "sort_review.html.j2": "review-sort",
        "phone_review.html.j2": "phone-free",
        "search.html.j2": "search",
        "browse.html.j2": "browse",
        "places.html.j2": "places",
        "people.html.j2": "people",
        "person.html.j2": "people",
        "slideshow.html.j2": "slideshow",
        "shrink.html.j2": "shrink",
        "history.html.j2": "history",
        "album.html.j2": ALBUMS_DOC,
    }
)
# The other language's link, written in that language: never translated.
_TWIN_LABELS: Final = MappingProxyType(
    {Locale.EN: "In English", Locale.FR: "En français"}
)


@dataclass(frozen=True, slots=True)
class PageHeader:
    """What the bar of a page shows."""

    doc: str  # its chapter, in the page's language
    twin: str  # the same chapter in the other language
    twin_locale: Locale
    twin_label: str
    home: bool  # opened from the home page: the way back is offered
    shared: bool = False  # served by the home server itself (0356): a plain link back
    assets: str = ASSETS_PREFIX

    @property
    def twin_lang(self) -> str:
        """The other language's code, for `hreflang` and `lang`.

        Returns:
            It, e.g. `fr`.
        """
        return self.twin_locale.value


def page_header(template: str) -> PageHeader:
    """The bar of a page, in the language in use.

    Args:
        template: The page's template, a key of `PAGE_STEPS`.

    Returns:
        Its links.

    Raises:
        KeyError: The page's action has no chapter (test_page_headers checks each).
    """
    wanted = PAGE_STEPS[template]
    doc = wanted if isinstance(wanted, Doc) else catalog().step(wanted).doc
    if doc is None:  # pragma: no cover - test_page_headers checks every page has one
        raise KeyError(template)
    here = active_locale()
    twin = Locale.EN if here is Locale.FR else Locale.FR
    return PageHeader(
        doc=served_url(doc, here),
        twin=served_url(doc, twin),
        twin_locale=twin,
        twin_label=_TWIN_LABELS[twin],
        home=bool(os.environ.get(LAUNCHER_STEPS_VARIABLE)),
        shared=keeps_server(),
    )


def headed_page(
    environment: Environment, template: str, values: Mapping[str, object]
) -> bytes:
    """Render a page with its bar.

    Args:
        environment: Where its template lives.
        template: The page's template, a key of `PAGE_STEPS`.
        values: What else it names.

    Returns:
        The page.
    """
    page = environment.get_template(template)
    return page.render(header=page_header(template), **values).encode()
