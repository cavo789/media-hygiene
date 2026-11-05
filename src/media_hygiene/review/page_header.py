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
from media_hygiene.cli.menu_entry import Doc, Space
from media_hygiene.cli.safety import PAGE_CAPTURED
from media_hygiene.constants import Locale
from media_hygiene.docs.served import served_url
from media_hygiene.i18n import _, active_locale
from media_hygiene.review.home_assets import ASSETS_PREFIX
from media_hygiene.review.shell import Shell, ShellAsk, page_shell
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
        "disk_space.html.j2": Doc(
            "commands/home/", "#disk-space", "#place-sur-le-disque"
        ),
        "tidy_empty.html.j2": Doc(
            "commands/home/", "#10-minutes-of-tidying", "#10-minutes-de-rangement"
        ),
        "near_review.html.j2": "review-near",
        "pairs_review.html.j2": "review-pairs",
        "unwanted_review.html.j2": "review-junk",
        "gone_review.html.j2": "review-gone",
        "intruders_review.html.j2": "review-intruders",
        "phone_review.html.j2": "phone-free",
        "search.html.j2": "search",
        "places.html.j2": "places",
        "people.html.j2": "people",
        "person.html.j2": "people",
        "slideshow.html.j2": "slideshow",
        "shrink.html.j2": "shrink",
        "history.html.j2": "history",
        "quarantine.html.j2": "undo-pick",
        "import_pick.html.j2": "import-pick",
        **{f"console_{name}.html.j2": name for name in PAGE_CAPTURED},
        "album.html.j2": ALBUMS_DOC,
        "album_edit.html.j2": ALBUMS_DOC,
    }
)
# The pages in the home page's frame (0491: the shell; 0492-0496 moved them); the
# phone's page keeps the thin bar (read-only, its own layout). Value: a tile page or a
# map with its own left column (the sidebar folded to its icons, the grid keeps its
# columns).
SHELL_PAGES: Final[Mapping[str, bool]] = MappingProxyType(
    {
        "album.html.j2": False,
        "disk_space.html.j2": False,
        "tidy_empty.html.j2": False,
        "album_edit.html.j2": True,
        "search.html.j2": True,
        "review.html.j2": True,
        "near_review.html.j2": True,
        "pairs_review.html.j2": True,
        "gone_review.html.j2": True,
        "intruders_review.html.j2": True,
        "unwanted_review.html.j2": True,
        "quarantine.html.j2": True,
        "import_pick.html.j2": True,
        "people.html.j2": True,
        "person.html.j2": True,
        "places.html.j2": True,
        "history.html.j2": False,
        **dict.fromkeys((f"console_{name}.html.j2" for name in PAGE_CAPTURED), False),
        "shrink.html.j2": False,
    }
)
# A page whose space is not its action's: no action opens it, or the faces are found
# (0495: *Find*, while `people` is listed under *Sort*).
_PAGE_SPACES: Final = MappingProxyType(
    {
        "album.html.j2": Space.SHARE,
        "album_edit.html.j2": Space.SHARE,
        "people.html.j2": Space.FIND,
        "person.html.j2": Space.FIND,
    }
)
# The other language's link, written in that language: never translated.
_TWIN_LABELS: Final = MappingProxyType(
    {Locale.EN: "In English", Locale.FR: "En français"}
)


@dataclass(frozen=True, slots=True)
class PageHeader:  # pylint: disable=too-many-instance-attributes  # one per link of the bar
    """What the bar of a page shows."""

    doc: str  # its chapter, in the page's language
    twin: str  # the same chapter in the other language
    twin_locale: Locale
    twin_label: str
    home: bool  # opened from the home page: the way back is offered
    shared: bool = False  # served by the home server itself (0356): a plain link back
    assets: str = ASSETS_PREFIX
    shell: Shell | None = None  # in the home page's frame (0491)

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
    space = _PAGE_SPACES.get(template) or (
        None if isinstance(wanted, Doc) else catalog().step(wanted).space
    )
    here = active_locale()
    twin = Locale.EN if here is Locale.FR else Locale.FR
    return PageHeader(
        doc=served_url(doc, here),
        twin=served_url(doc, twin),
        twin_locale=twin,
        twin_label=_TWIN_LABELS[twin],
        home=bool(os.environ.get(LAUNCHER_STEPS_VARIABLE)),
        shared=keeps_server(),
        shell=(
            page_shell(ShellAsk(space, compact=SHELL_PAGES[template]), _("Home page"))
            if template in SHELL_PAGES
            else None
        ),
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
