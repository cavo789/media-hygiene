"""0615: from the phone, the slideshow's help fits a screen and names no command."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

import media_hygiene
from media_hygiene.cli.home_state import home_state
from media_hygiene.cli.menu_catalog_share import DRIVE_HELP, TV_HELP
from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.services.home import home_page
from tests.support.runtime import make_locations, make_runtime
from tests.unit.test_documentation import DOCUMENTATION, anchors

_MOST_WORDS: Final = 120
_OPENINGS: Final = {"en": "## On the sofa\n", "fr": "## Dans le canapé\n"}
_ASKED: Final = {"en": "## What are you looking for?", "fr": "## Que cherchez-vous ?"}


def _page(locale: str, page: str = "commands/slideshow.md") -> str:
    """A page of the documentation."""
    return (DOCUMENTATION / locale / page).read_text(encoding="utf-8")


@pytest.mark.parametrize("locale", ["en", "fr"])
def test_the_phone_section_is_short_and_has_no_command(locale: str) -> None:
    """What the phone's link lands on, up to the next chapter."""
    text = _page(locale)
    section = text.split(_OPENINGS[locale])[1].split("\n## ")[0]
    assert len(section.split()) <= _MOST_WORDS
    assert not re.search(r"\bdocker\b|\bmh\b", section)
    assert "8089" in section


@pytest.mark.parametrize("locale", ["en", "fr"])
@pytest.mark.parametrize(
    "page",
    [
        "commands/slideshow.md",
        "commands/library.md",
        "commands/home.md",
        "reference-albums.md",
    ],
)
def test_long_pages_open_on_the_question(locale: str, page: str) -> None:
    """Before any explanation: the first chapter of the page."""
    first = re.search(r"^## .*$", _page(locale, page), re.MULTILINE)
    assert first
    assert first[0] == _ASKED[locale]


def test_the_anchors_exist() -> None:
    """Both chapters, in both languages."""
    for doc in (TV_HELP, DRIVE_HELP):
        assert doc.en.removeprefix("#") in anchors(
            DOCUMENTATION / "en/commands/slideshow.md"
        )
        assert doc.fr.removeprefix("#") in anchors(
            DOCUMENTATION / "fr/commands/slideshow.md"
        )


@pytest.mark.parametrize("locale", [Locale.EN, Locale.FR])
def test_the_phone_view_gets_the_anchor(tmp_path: Path, locale: Locale) -> None:
    """The home page's state carries the chapter, and the family view draws it."""
    with using(locale):
        state = home_state(make_runtime(make_locations(tmp_path)))
        anchor = TV_HELP.fr if locale is Locale.FR else TV_HELP.en
        assert state.tv_help.endswith(f"commands/slideshow/{anchor}")
        assert "S.tv_help" in home_page(remote=True).decode()


def test_the_remote_on_a_phone_opens_the_gestures() -> None:
    """The script of the remote swaps its help link on a narrow screen."""
    root = Path(media_hygiene.__file__).parent
    script = (root / "slideshow/templates/slideshow.js.j2").read_text(encoding="utf-8")
    assert "phone_help | tojson" in script
