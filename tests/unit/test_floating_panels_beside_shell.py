"""Floating panels open beside the shell's menu, never under it (0624).

*More keys* and search's *My folders* tree are `position: fixed`: they ignore the body's
`padding-left`, so their `left` and width must take the menu's width into account.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

TEMPLATES: Final = Path(__file__).parents[2] / "src" / "media_hygiene"
SHELL: Final = TEMPLATES / "review" / "templates" / "shell.css.j2"
OFFSET: Final = "var(--mh-shell-left, 0px)"


def _rule(path: Path, selector: str) -> str:
    text = path.read_text(encoding="utf-8")
    start = text.index(selector + " {")
    return text[start : text.index("}", start)]


def test_the_shell_offset_is_set_only_on_a_shelled_page() -> None:
    """Outside the shell the variable is unset, so the fallback 0px applies."""
    text = SHELL.read_text(encoding="utf-8")
    assert re.search(
        r"html\.mh-shelled \{[^}]*--mh-shell-left: var\(--mh-shell-w\)", text
    )
    assert not re.search(r":root[^{]*\{[^}]*--mh-shell-left", text)


@pytest.mark.parametrize(
    ("relative", "selector"),
    [
        ("review/templates/keys.css.j2", "#moreKeys[open] > dl"),
        ("search/templates/search.html.j2", "#folders[open] > #tree"),
    ],
)
def test_a_floating_panel_starts_after_the_menu(relative: str, selector: str) -> None:
    """Its left edge and its width both subtract the menu's width."""
    rule = _rule(TEMPLATES / relative, selector)
    assert f"left: calc({OFFSET} + 16px)" in rule
    assert f"calc(100vw - {OFFSET} - 32px)" in rule
