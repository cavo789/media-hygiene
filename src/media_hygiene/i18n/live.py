"""A page drawn once per language: the language picked on a page applies live (0644).

A server draws its page at start; once `install()` changes the language, the next load
draws it again in the new one (kept per language: switching back costs nothing).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.i18n import active_locale

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.constants import Locale


class PerLocale:
    """Draws a page in the language in use, once per language."""

    __slots__ = ("_draw", "_drawn")

    def __init__(self, draw: Callable[[], bytes]) -> None:
        """Keep how to draw the page.

        Args:
            draw: Renders it in the language in use.
        """
        self._draw = draw
        self._drawn: dict[Locale, bytes] = {}

    def __call__(self) -> bytes:
        """The page, in the language in use.

        Returns:
            Its bytes.
        """
        locale = active_locale()
        if locale not in self._drawn:
            self._drawn[locale] = self._draw()
        return self._drawn[locale]


def page_of(page: bytes | Callable[[], bytes]) -> bytes:
    """A page drawn once, or in the language in use.

    Args:
        page: Its bytes, or a `PerLocale`.

    Returns:
        Its bytes.
    """
    return page if isinstance(page, bytes) else page()
