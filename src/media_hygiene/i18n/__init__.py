"""Internationalisation: gettext `.po` catalogs loaded at runtime, English by default.

Every user-facing string goes through `_()` (or `ngettext()` for plurals) so that
`pybabel extract` finds it. The active translation lives in a context variable,
installed once at start-up by `install()`.
"""

from __future__ import annotations

import gettext
from contextlib import contextmanager
from contextvars import ContextVar
from typing import TYPE_CHECKING

from media_hygiene.constants import Locale
from media_hygiene.i18n.catalog import load_translations

if TYPE_CHECKING:
    from collections.abc import Iterator

_LOCALE: ContextVar[Locale] = ContextVar("media_hygiene_locale", default=Locale.EN)
_ACTIVE: ContextVar[gettext.NullTranslations] = ContextVar(
    "media_hygiene_translations",
    default=gettext.NullTranslations(),  # noqa: B039 - stateless, safe to share
)


def install(locale: Locale) -> gettext.NullTranslations:
    """Activate the catalog of `locale` for every later `_()` call.

    Args:
        locale: Language to activate.

    Returns:
        The translations object, also usable by Jinja's i18n extension.
    """
    translations = load_translations(locale)
    _ACTIVE.set(translations)
    _LOCALE.set(locale)
    return translations


@contextmanager
def using(locale: Locale) -> Iterator[None]:
    """Translate into `locale` for a while, then restore the language in use.

    Args:
        locale: Language to use inside the `with` block.

    Yields:
        Nothing: `_()` translates into `locale` until the block ends.
    """
    translations = _ACTIVE.set(load_translations(locale))
    language = _LOCALE.set(locale)
    try:
        yield
    finally:
        _ACTIVE.reset(translations)
        _LOCALE.reset(language)


def active_locale() -> Locale:
    """Return the language currently in use (numbers are formatted after it).

    Returns:
        The locale installed last, English before `install()`.
    """
    return _LOCALE.get()


def active() -> gettext.NullTranslations:
    """Return the translations currently in use.

    Returns:
        The active translations (a no-op catalog before `install()`).
    """
    return _ACTIVE.get()


def _(message: str) -> str:
    """Translate `message` into the active language.

    Args:
        message: English source text.

    Returns:
        The translation, or `message` itself when none exists.
    """
    return _ACTIVE.get().gettext(message)


def ngettext(singular: str, plural: str, count: int) -> str:
    """Translate a message whose wording depends on `count`.

    Args:
        singular: English text for one item.
        plural: English text for several items.
        count: Number of items, selecting the plural form.

    Returns:
        The translation matching `count`.
    """
    return _ACTIVE.get().ngettext(singular, plural, count)
