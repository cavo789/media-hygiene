"""The documented Czkawka command keeps the same scope as media-hygiene."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from media_hygiene.constants import MEDIA_EXTENSIONS

ROOT = Path(__file__).resolve().parents[2]
CZKAWKA_EXTENSIONS = re.compile(r"^\s*-x (?P<list>[a-z0-9,]+)$", re.MULTILINE)


@pytest.mark.parametrize("locale", ["en", "fr"])
def test_czkawka_scans_the_same_extensions(locale: str) -> None:
    """A new extension in the code must be added to the documented command too."""
    page = ROOT / "documentation" / locale / "13-second-opinion.md"
    found = CZKAWKA_EXTENSIONS.search(page.read_text(encoding="utf-8"))
    assert found is not None
    expected = {extension.lstrip(".") for extension in MEDIA_EXTENSIONS}
    assert set(found["list"].split(",")) == expected
