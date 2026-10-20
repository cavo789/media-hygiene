"""A chapter's address: served by the tool when its docs are there, else the site's.

The pages the tool serves link the docs of the version that runs (`/docs/…`, any
page's server answers it); the terminal and the reports opened from disk keep the
public site's address: no server answers there.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.constants import Locale
from media_hygiene.docs.pages import DOCS_PREFIX, INDEX_FILE
from media_hygiene.docs.shelf import docs_root
from media_hygiene.i18n import active_locale

if TYPE_CHECKING:
    from media_hygiene.cli.menu_entry import Doc


def served_url(doc: Doc, locale: Locale | None = None) -> str:
    """A chapter's address for a page the tool serves.

    Args:
        doc: The chapter.
        locale: Its language; None: the language in use.

    Returns:
        `/docs/<locale>/<page><anchor>` when the docs are there; else the site's.
    """
    language = locale or active_locale()
    if docs_root() is None:
        return doc.url(language)
    anchor = doc.fr if language is Locale.FR else doc.en
    return f"{DOCS_PREFIX}{language.value}/{doc.page}{anchor}"


def served_index() -> str | None:
    """The index the palette of the home page searches, in the language in use.

    Returns:
        `/docs/<locale>/index.json`; None without docs.
    """
    if docs_root() is None:
        return None
    return f"{DOCS_PREFIX}{active_locale().value}/{INDEX_FILE}"
