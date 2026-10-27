"""A paired phone's home page is the family's door: read-only, the photos first (0293).

Decided 2026-10-23: one page, its acting stages (import, clean, sort, back up and the
tools that change files) hidden from a paired phone; the PC keeps the whole cycle.
"""

from __future__ import annotations

import json
import re

from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.services.home import home_page


def _texts(page: str) -> dict[str, str]:
    """The texts the page's script holds."""
    found = re.search(r"const T = (\{.*?\});\n", page)
    assert found
    texts: dict[str, str] = json.loads(found[1])
    return texts


def test_the_phone_sees_only_find_and_no_tool() -> None:
    """The stages but Find and every tool are dropped when the page is remote."""
    page = home_page(remote=True).decode()
    assert "const REMOTE = true;" in page
    assert 'const FAMILY_STAGE = "find";' in page
    assert (
        "if (REMOTE) { STAGES = STAGES.filter((space) => space.id === FAMILY_STAGE);"
        " TOOLS = []; }"
    ) in page


def test_the_phone_home_draws_the_family_view_first() -> None:
    """No next step, cycle, findings or banners: the title, Find, albums, facts."""
    page = home_page(remote=True).decode()
    assert "if (REMOTE) return familyHome();" in page
    start = page.index("function familyHome()")
    family = page[start : page.index("function viewHome()")]
    assert "PHONE_PAGES[action.command]" in family
    for acting in ("hero()", "STAGES.map(station)", "findings()", "Banner()"):
        assert acting not in family


def test_the_title_in_both_languages() -> None:
    """*Our photos* / *Nos photos*, never a family's name."""
    assert _texts(home_page(remote=True).decode())["familyTitle"] == "Our photos"
    with using(Locale.FR):
        texts = _texts(home_page(remote=True).decode())
    assert texts["familyTitle"] == "Nos photos"
