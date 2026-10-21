"""Where a link of documentation/ leads: for the site's hooks and the docs in the image.

The pages are written for GitHub first: their anchors keep accents (`#étape-1`), each
page links its twin in the other language (`../../fr/…`), and some links point at
files outside documentation/ (the CI). The public site (`.config/mkdocs/hooks.py`) and
the docs rendered into the image (`render`) resolve them here, so the two never drift.
Standard library only: MkDocs loads this file by its path, outside the package.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Callable

BLOB: Final = "https://github.com/cavo789/media-hygiene/blob/main"
# `](target#anchor)` of a Markdown link or image.
MARKDOWN_LINK: Final = re.compile(
    r"(?P<head>\]\()(?P<target>[^)\s#]+)(?P<anchor>#[^)\s]*)?\)"
)
EXTERNAL: Final = ("http://", "https://", "mailto:")
DEFAULT_LOCALE: Final = "en"  # the site's root; the others under /<locale>/
INDEX: Final = "README.md"
SLUG_CASE: Final = "lower"  # GitHub's anchors: lower case, accents kept
MARKDOWN: Final = ".md"
_NOWHERE: Final = PurePosixPath()


class LinkKind(StrEnum):
    """Where a link leads."""

    OUTSIDE = "outside"  # another site
    PAGE = "page"  # a page of documentation/
    FILE = "file"  # another file of documentation/ (a screenshot)
    REPOSITORY = "repository"  # a file of the repository outside documentation/
    KEEP = "keep"  # nothing to resolve: left as written


@dataclass(frozen=True, slots=True)
class LinkSource:
    """The page holding a link."""

    docs: Path  # documentation/, resolved
    page: Path  # the page's file, resolved


@dataclass(frozen=True, slots=True)
class LinkTarget:
    """What a link leads to: relative to documentation/ or to the repository."""

    kind: LinkKind
    path: PurePosixPath = _NOWHERE


def resolve(source: LinkSource, target: str) -> LinkTarget:
    """Tell where a link written in a page leads.

    Args:
        source: The page holding it.
        target: The link, without its anchor.

    Returns:
        Its kind, and its path inside documentation/ or the repository.
    """
    if target.startswith(EXTERNAL):
        return LinkTarget(LinkKind.OUTSIDE)
    if not target:
        return LinkTarget(LinkKind.KEEP)
    resolved = (source.page.parent / target).resolve()
    if resolved.is_relative_to(source.docs):
        path = PurePosixPath(*resolved.relative_to(source.docs).parts)
        kind = LinkKind.PAGE if resolved.suffix == MARKDOWN else LinkKind.FILE
        return LinkTarget(kind, path)
    repository = source.docs.parent
    if resolved.is_relative_to(repository):
        path = PurePosixPath(*resolved.relative_to(repository).parts)
        return LinkTarget(LinkKind.REPOSITORY, path)
    return LinkTarget(LinkKind.KEEP)


def page_parts(page_path: PurePosixPath) -> tuple[str, tuple[str, ...]]:
    """Split a page of documentation/ into its language and its address's parts.

    Args:
        page_path: E.g. `fr/start/01-first-audit.md`.

    Returns:
        E.g. `("fr", ("start", "01-first-audit"))`; a folder's README has no last part.
    """
    locale, *parts = page_path.parts
    *folders, name = parts
    tail = () if name == INDEX else (name.removesuffix(MARKDOWN),)
    return locale, (*folders, *tail)


def blob_url(path: PurePosixPath) -> str:
    """The address on GitHub of a file of the repository.

    Args:
        path: Relative to the repository.

    Returns:
        Its address.
    """
    return f"{BLOB}/{path}"


def slugifier() -> Callable[..., str]:
    """The slugs of the headings, GitHub's: the site and the image use this one.

    Returns:
        pymdownx's slugify, lower case (the `docs` dependency group only).
    """
    # The docs group only: never imported by the shipped image.
    from pymdownx.slugs import (  # noqa: PLC0415  # pylint: disable=import-outside-toplevel
        slugify,
    )

    return slugify(case=SLUG_CASE)  # type: ignore[no-any-return]
