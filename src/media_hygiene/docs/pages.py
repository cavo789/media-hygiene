"""The index of a language's docs: its menu, each page's title, headings and route.

Written by `render` when the image is built (`index.json`, next to the fragments in
`pages/` and the screenshots in `images/`), read by `shelf` when a page is served.
Standard library only: the build stage holds the `docs` group, not the tool's.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Final

from media_hygiene.docs.links import page_parts

DOCS_PREFIX: Final = "/docs/"
INDEX_FILE: Final = "index.json"
PAGES_DIR: Final = "pages"
IMAGES_DIR: Final = "images"
FRAGMENT_SUFFIX: Final = ".html"


@dataclass(frozen=True, slots=True)
class Heading:
    """A heading of a page: `h2` or `h3`, with its anchor."""

    level: int
    anchor: str
    title: str


@dataclass(frozen=True, slots=True)
class DocPage:
    """A page: its file in documentation/<locale>/, title, route, headings."""

    path: str  # e.g. `commands/audit.md`
    title: str
    route: str  # e.g. `/docs/en/commands/audit/`
    headings: tuple[Heading, ...] = ()

    @property
    def fragment(self) -> str:
        """Its HTML fragment, relative to the language's folder.

        Returns:
            E.g. `pages/commands/audit.html`.
        """
        name = PurePosixPath(self.path).with_suffix(FRAGMENT_SUFFIX)
        return f"{PAGES_DIR}/{name}"


@dataclass(frozen=True, slots=True)
class NavSection:
    """A section of the menu, as `nav` of mkdocs.yml lists it; untitled at the top."""

    title: str
    pages: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DocIndex:
    """The docs of one language: the menu, then every page in the menu's order."""

    locale: str
    sections: tuple[NavSection, ...]
    pages: tuple[DocPage, ...]

    def page(self, path: str) -> DocPage | None:
        """The page of a file.

        Args:
            path: E.g. `commands/audit.md`.

        Returns:
            It, or None.
        """
        return next((page for page in self.pages if page.path == path), None)

    def at_route(self, route: str) -> DocPage | None:
        """The page a route names, its trailing slash optional.

        Args:
            route: E.g. `/docs/en/commands/audit/`.

        Returns:
            It, or None.
        """
        wanted = route.rstrip("/") + "/"
        return next((page for page in self.pages if page.route == wanted), None)

    def neighbours(self, page: DocPage) -> tuple[DocPage | None, DocPage | None]:
        """The pages before and after one, in the menu's order.

        Args:
            page: A page of this index.

        Returns:
            The previous page and the next one; None at either end.
        """
        at = self.pages.index(page)
        before = self.pages[at - 1] if at > 0 else None
        after = self.pages[at + 1] if at + 1 < len(self.pages) else None
        return before, after


def route_of(locale: str, path: str) -> str:
    """The route of a page served by the tool.

    Args:
        locale: Its language, e.g. `fr`.
        path: Its file in documentation/<locale>/, e.g. `start/01-first-audit.md`.

    Returns:
        E.g. `/docs/fr/start/01-first-audit/`; `/docs/fr/` for the README.
    """
    _locale, parts = page_parts(PurePosixPath(locale, path))
    return "/".join((DOCS_PREFIX.rstrip("/"), locale, *parts)) + "/"
