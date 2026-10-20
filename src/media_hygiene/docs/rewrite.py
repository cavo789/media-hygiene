"""The links of a rendered page, pointed at the routes the tool serves (build time).

A page of documentation/ links others by their file (`../commands/audit.md#…`) and
shows screenshots by theirs (`../images/home.webp`). In the image, a page is
`/docs/<locale>/<page>/` and a screenshot `/docs/<locale>/images/<name>`; anchors are
kept. A link to another site opens a new tab; an image from another site is dropped:
a page served by the tool asks nothing outside (its CSP allows `self` only).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from media_hygiene.docs.links import LinkKind, LinkSource, blob_url, resolve
from media_hygiene.docs.pages import DOCS_PREFIX, IMAGES_DIR, route_of

if TYPE_CHECKING:
    from media_hygiene.docs.links import LinkTarget

_TAG: Final = re.compile(r"<(?P<name>a|img)\s[^>]*>")
_ATTRIBUTE: Final = re.compile(
    r'(?P<attr>href|src)="(?P<target>[^"#]*)(?P<anchor>#[^"]*)?"'
)
_SOURCES: Final = "documentation"  # the folder of the pages, in the repository
_NEW_TAB: Final = ' target="_blank" rel="noopener"'
# `<!-- capture: … -->` then its code block: a console output, shown as a terminal.
_CAPTURE: Final = re.compile(r"<!-- capture:[^>]*-->\s*<pre class=\"highlight\">")
_CAPTURED: Final = '<pre class="highlight capture">'


def rewrite_html(html: str, source: LinkSource) -> str:
    """Point every link and image of a rendered page at its route.

    Args:
        html: The page, rendered.
        source: Its file, and documentation/.

    Returns:
        The page, its links and images rewritten, its captures marked.
    """

    def tag(found: re.Match[str]) -> str:
        """Rewrite one `<a>` or `<img>`.

        Args:
            found: The tag.

        Returns:
            It, rewritten; empty for an image from another site.
        """
        attribute = _ATTRIBUTE.search(found[0])
        if attribute is None:
            return found[0]
        target = resolve(source, attribute["target"])
        address = _address(target, attribute["target"])
        if address is None:
            return found[0]
        anchor = attribute["anchor"] or ""
        written = f'{attribute["attr"]}="{address}{anchor}"'
        rewritten = found[0].replace(attribute[0], written, 1)
        if target.kind is LinkKind.KEEP or address.startswith(DOCS_PREFIX):
            return rewritten
        if found["name"] == "img":
            return ""  # outside the tool: never asked for
        return rewritten[:-1] + _NEW_TAB + ">"

    return _CAPTURE.sub(_CAPTURED, _TAG.sub(tag, html))


def _address(target: LinkTarget, written: str) -> str | None:
    """The address a link leads to, once served by the tool.

    Args:
        target: Where it leads.
        written: The link as written.

    Returns:
        The address; None to leave the tag as it is (an anchor of the same page).
    """
    match target.kind:
        case LinkKind.OUTSIDE:
            return written
        case LinkKind.KEEP:
            return written or None
        case LinkKind.PAGE:
            locale, *parts = target.path.parts
            return route_of(locale, "/".join(parts))
        case LinkKind.FILE:
            if target.path.parent.name == IMAGES_DIR:
                return f"{DOCS_PREFIX}{target.path}"
            return blob_url(_SOURCES / target.path)
        case LinkKind.REPOSITORY:
            return blob_url(target.path)
