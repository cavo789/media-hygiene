"""Internationalisation: gettext `.po` catalogs loaded at runtime, English by default.

Every user-facing string goes through `_()` (or `ngettext()` for plurals) so that
`pybabel extract` finds it. `install()` chooses the language once, at start-up, for
the whole process: every thread reads it, those started by the code as well as the
workers of a pool, which copy no context. `using()` changes it for a while, in its
own thread or task only (a context variable), without touching the others.
"""

from __future__ import annotations

import gettext
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import Locale
from media_hygiene.i18n.catalog import load_translations

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(frozen=True, slots=True)
class _Language:
    """A locale and its catalog."""

    locale: Locale
    translations: gettext.NullTranslations


class _Installed:
    """The language of the process, as `install()` chose it last.

    The one piece of process state of this module, on purpose: a new thread starts
    with an empty context, so a context variable alone would leave it in English.
    """

    __slots__ = ("language",)

    def __init__(self) -> None:
        """English, until `install()` chooses."""
        self.language = _Language(Locale.EN, gettext.NullTranslations())


_INSTALLED: Final = _Installed()
_USING: ContextVar[_Language | None] = ContextVar("media_hygiene_using", default=None)


def _current() -> _Language:
    """The language of `using()` in this thread or task, else the process's.

    Returns:
        The language in use.
    """
    return _USING.get() or _INSTALLED.language


def install(locale: Locale) -> gettext.NullTranslations:
    """Activate the catalog of `locale` for every later `_()` call, in every thread.

    Args:
        locale: Language to activate.

    Returns:
        The translations object, also usable by Jinja's i18n extension.
    """
    translations = load_translations(locale)
    _INSTALLED.language = _Language(locale, translations)
    return translations


@contextmanager
def using(locale: Locale) -> Iterator[None]:
    """Translate into `locale` for a while, in this thread or task, then restore.

    Args:
        locale: Language to use inside the `with` block.

    Yields:
        Nothing: `_()` translates into `locale` until the block ends.
    """
    token = _USING.set(_Language(locale, load_translations(locale)))
    try:
        yield
    finally:
        _USING.reset(token)


def active_locale() -> Locale:
    """Return the language currently in use (numbers are formatted after it).

    Returns:
        The locale installed last, English before `install()`.
    """
    return _current().locale


def active() -> gettext.NullTranslations:
    """Return the translations currently in use.

    Returns:
        The active translations (a no-op catalog before `install()`).
    """
    return _current().translations


def _(message: str) -> str:
    """Translate `message` into the active language.

    Args:
        message: English source text.

    Returns:
        The translation, or `message` itself when none exists.
    """
    return _current().translations.gettext(message)


def ngettext(singular: str, plural: str, count: int) -> str:
    """Translate a message whose wording depends on `count`.

    Args:
        singular: English text for one item.
        plural: English text for several items.
        count: Number of items, selecting the plural form.

    Returns:
        The translation matching `count`.
    """
    return _current().translations.ngettext(singular, plural, count)
