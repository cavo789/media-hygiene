"""Translations: runtime catalogs, early locale resolution, catalog completeness."""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from importlib.resources import files
from typing import TYPE_CHECKING

import polib
import pytest

from media_hygiene.console.formatting import human_number
from media_hygiene.constants import Locale
from media_hygiene.i18n import _, active_locale, install, ngettext, using
from media_hygiene.i18n.bootstrap import locale_from_argv, resolve_locale

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

LOCALES = files("media_hygiene.i18n").joinpath("locales")


def test_french_is_loaded_from_the_po_file() -> None:
    """Installing French translates simple and plural messages."""
    install(Locale.FR)
    assert _("Nothing was changed.") == "Rien n'a été modifié."
    assert ngettext("{count} report deleted.", "{count} reports deleted.", 2) == (
        "{count} rapports supprimés."
    )


def test_english_is_the_source_language() -> None:
    """English needs no catalog: messages come back unchanged."""
    install(Locale.EN)
    assert _("Nothing was changed.") == "Nothing was changed."


def _spoken() -> tuple[str, str]:
    """A message and a number, as the calling thread renders them."""
    return _("Nothing was changed."), human_number(51818)


def test_a_thread_speaks_the_language_installed() -> None:
    """A thread or a pool worker started after `install()` translates and formats alike.

    A new thread starts with an empty context: the language is the process's.
    """
    install(Locale.FR)
    french = ("Rien n'a été modifié.", "51.818")
    told: list[tuple[str, str]] = []
    thread = threading.Thread(target=lambda: told.append(_spoken()))
    thread.start()
    thread.join()
    with ThreadPoolExecutor(1) as pool:
        told.append(pool.submit(_spoken).result())
    assert told == [french, french]


def test_using_changes_the_language_of_its_own_thread_only() -> None:
    """`using()` is local: another thread keeps the language installed meanwhile."""
    install(Locale.FR)
    with using(Locale.EN), ThreadPoolExecutor(1) as pool:
        assert active_locale() is Locale.EN
        assert pool.submit(active_locale).result() is Locale.FR
    assert active_locale() is Locale.FR


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["--locale", "fr", "audit"], Locale.FR),
        (["audit", "--locale=fr"], Locale.FR),
        (["--locale", "xx"], None),
        (["--locale"], None),
        (["audit"], None),
    ],
)
def test_locale_from_argv(argv: list[str], expected: Locale | None) -> None:
    """`--locale` is found anywhere; invalid values are left to Typer."""
    assert locale_from_argv(argv) is expected


def test_resolve_locale_falls_back_to_config(
    locations: Locations,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without `--locale`, the configuration decides; a broken one means English.

    A file refused for another key keeps its language: the error reads in French.
    """
    monkeypatch.setenv("MEDIA_HYGIENE_CONFIG_DIR", str(locations.config_dir))
    locations.config_file.write_text('[general]\nlocale = "fr"\n')
    assert resolve_locale(["audit"]) is Locale.FR
    locations.config_file.write_text('[general]\nlocale = "fr"\ntimezon = "UTC"\n')
    assert resolve_locale(["audit"]) is Locale.FR
    locations.config_file.write_text('[general]\nlocale = "de"\n')
    assert resolve_locale(["audit"]) is Locale.EN
    locations.config_file.write_text("not = [valid")
    assert resolve_locale(["audit"]) is Locale.EN


def test_french_catalog_is_complete() -> None:
    """Every message of the template has a non-fuzzy French translation."""
    template = polib.pofile(LOCALES.joinpath("media_hygiene.pot").read_text("utf-8"))
    french = polib.pofile(
        LOCALES.joinpath("fr", "LC_MESSAGES", "media_hygiene.po").read_text("utf-8"),
    )
    translated = {entry.msgid for entry in french.translated_entries()}
    missing = [entry.msgid for entry in template if entry.msgid not in translated]
    assert missing == []
    assert french.fuzzy_entries() == []
