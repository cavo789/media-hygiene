"""0349: the albums page points at the chapter that explains albums and the page."""

from __future__ import annotations

from typing import Final

import pytest

from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.services.album_pages import album_page
from tests.unit.test_documentation import DOCUMENTATION

_CHAPTER: Final = "reference-albums"


@pytest.mark.parametrize("locale", list(Locale))
def test_the_page_names_the_chapter_in_its_language(locale: Locale) -> None:
    """The address the empty state links to is the chapter of the page's language."""
    with using(locale):
        page = album_page().decode()
    prefix = "fr/" if locale is Locale.FR else ""
    assert f"{prefix}{_CHAPTER}/" in page
    assert (DOCUMENTATION / locale.value / f"{_CHAPTER}.md").is_file()


def test_the_page_wears_the_shared_bar_with_a_plain_way_back() -> None:
    """0342: the bar of every page, its way back a plain link; ← Albums below."""
    page = album_page().decode()
    assert page.count('class="mh-bar"') == 1
    assert 'id="homeLink" href="/" data-shared="1"' in page
    assert 'id="back" href="#" hidden>← Albums' in page
    assert f"{_CHAPTER}/" in page.split('class="mh-doc"')[1]


def test_the_page_pings_the_server_and_says_when_it_stopped() -> None:
    """0411: PC or paired phone, its pings keep the server up; it says when it stops.

    A paired phone's `POST /api/alive` passes `lan_app` (0416, `test_home_lan`).
    """
    page = album_page().decode()
    assert '"/api/alive"' in page
    assert 'id="mhStopped"' in page
