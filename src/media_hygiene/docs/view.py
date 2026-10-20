"""A page of the docs in the home page's shell: its menu, contents, neighbours, twin.

The body is the fragment rendered when the image was built; around it, the sidebar
lists the menu of `mkdocs.yml`, the top bar switches to the same page in the other
language, the side column lists the page's headings, the foot its previous and next
pages. The same tokens, theme switch and meerkat as the home page.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from markupsafe import Markup

from media_hygiene.constants import Locale
from media_hygiene.docs.links import INDEX
from media_hygiene.docs.pages import route_of
from media_hygiene.docs.shelf import doc_index
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.home_assets import ASSETS_PREFIX
from media_hygiene.review.presence import ALIVE_SECONDS, PRESENCE_PATH

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.docs.pages import DocIndex, DocPage

_PACKAGE: Final = "media_hygiene.docs"
_TEMPLATE: Final = "doc.html.j2"
# The other language's link, written in that language: never translated.
_TWIN_LABELS: Final = MappingProxyType({Locale.EN: "EN", Locale.FR: "FR"})
_TWIN_TITLES: Final = MappingProxyType(
    {Locale.EN: "In English", Locale.FR: "En français"}
)


@dataclass(frozen=True, slots=True)
class DocView:
    """A page to show: None for a route that names none."""

    root: Path  # the rendered docs
    locale: Locale
    page: DocPage | None


@dataclass(frozen=True, slots=True)
class NavItem:
    """A page of the sidebar."""

    title: str
    route: str
    current: bool


def render_doc_page(view: DocView) -> bytes:
    """Render a page of the docs, or the meerkat saying it does not exist.

    Args:
        view: The docs, the language, the page.

    Returns:
        The HTML page.
    """
    index = doc_index(view.root, view.locale)
    page = view.page
    twin = Locale.EN if view.locale is Locale.FR else Locale.FR
    before, after = index.neighbours(page) if page else (None, None)
    template = translated_environment(_PACKAGE, escaped=("html", "j2")).get_template(
        _TEMPLATE
    )
    return template.render(
        lang=view.locale.value,
        page=page,
        body=_fragment(view, page),
        sections=_sections(index, page),
        headings=page.headings if page else (),
        before=before,
        after=after,
        home=route_of(view.locale.value, INDEX),
        twin={
            "route": route_of(twin.value, page.path if page else INDEX),
            "label": _TWIN_LABELS[twin],
            "title": _TWIN_TITLES[twin],
            "lang": twin.value,
        },
        paths={"assets": ASSETS_PREFIX, "alive": PRESENCE_PATH},
        alive_ms=ALIVE_SECONDS * 1000,
    ).encode()


def _fragment(view: DocView, page: DocPage | None) -> Markup:
    """The body of a page, as rendered when the image was built: trusted HTML.

    Args:
        view: The docs and the language.
        page: The page; None for none.

    Returns:
        Its HTML; empty without a page.
    """
    if page is None:
        return Markup()
    fragment = view.root / view.locale.value / page.fragment
    return Markup(fragment.read_text(encoding="utf-8"))  # noqa: S704  # built from documentation/


def _sections(
    index: DocIndex, page: DocPage | None
) -> tuple[tuple[str, tuple[NavItem, ...]], ...]:
    """The menu of the sidebar, the page shown marked.

    Args:
        index: The docs of the language.
        page: The page shown, if any.

    Returns:
        Each section's title and pages.
    """
    return tuple(
        (
            section.title,
            tuple(
                NavItem(found.title, found.route, found == page)
                for path in section.pages
                if (found := index.page(path)) is not None
            ),
        )
        for section in index.sections
    )
