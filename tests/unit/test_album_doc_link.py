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
