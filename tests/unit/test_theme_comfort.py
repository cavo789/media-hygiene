"""The comfort the shared theme gives every page (0669), checked from the CSS alone.

Contrast of the text colours over their backgrounds in both themes, a ring on what Tab
reaches, no long motion when the system asks for less. The browser checks of the pages
themselves are `tests/support/comfort_walk.py` (CI).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

from tests.support.page_render import render_page

_SRC: Final = Path(__file__).resolve().parents[2] / "src" / "media_hygiene"
_TOKENS: Final = (_SRC / "assets" / "theme" / "tokens.css").read_text("utf-8")
_TEMPLATES: Final = _SRC / "review" / "templates"
_MIN: Final = 4.5
_DARK_AT: Final = _TOKENS.index(':root[data-theme="dark"]')
_DARK_END: Final = _TOKENS.index("/* The colour names")
_DECL: Final = re.compile(r"--([\w-]+):\s*(#[0-9a-fA-F]{6}|var\(--[\w-]+\))\s*;")
# (text token, background token): what the pages draw as text. `--bg`, `--card`
# and `--chip` are mk-n-0, mk-surface and mk-sunken.
PAIRS: Final = (
    ("mk-ink", "mk-n-0"),
    ("mk-ink", "mk-surface"),
    ("mk-ink", "mk-sunken"),
    ("mk-ink-soft", "mk-n-0"),
    ("mk-ink-soft", "mk-surface"),
    ("mk-ink-soft", "mk-sunken"),
    ("mk-primary", "mk-n-0"),
    ("mk-primary", "mk-surface"),
    ("mk-primary", "mk-sunken"),
    ("mk-on-primary", "mk-primary"),
    ("mk-on-danger", "mk-danger-line"),
    ("mk-danger-line", "mk-n-0"),
    ("mk-danger-line", "mk-surface"),
    ("mk-tip-line", "mk-n-0"),
    ("mk-tip-line", "mk-surface"),
    ("mk-warn-line", "mk-surface"),
    ("mk-info-line", "mk-surface"),
    ("mk-info-fg", "mk-info-bg"),
    ("mk-tip-fg", "mk-tip-bg"),
    ("mk-note-fg", "mk-note-bg"),
    ("mk-warn-fg", "mk-warn-bg"),
    ("mk-danger-fg", "mk-danger-bg"),
    ("mk-key-fg", "mk-key-bg"),
    ("mh-frame-ink", "mh-frame"),
    ("mh-frame-soft", "mh-frame"),
    ("mh-on-apricot", "mh-apricot"),
    ("mh-ai-fg", "mh-ai-bg"),
)


def _theme(*, dark: bool) -> dict[str, str]:
    """The colour tokens of a theme (the dark one overrides the light one)."""
    colours = dict(_DECL.findall(_TOKENS[: _TOKENS.index("@media")]))
    if dark:
        colours.update(_DECL.findall(_TOKENS[_DARK_AT:_DARK_END]))
    return {name: _resolved(colours, name) for name in colours}


def _resolved(colours: dict[str, str], name: str) -> str:
    """A token's colour, following `var(--other)` aliases."""
    value = colours[name]
    return _resolved(colours, value[6:-1]) if value.startswith("var(") else value


def _luminance(colour: str) -> float:
    """WCAG relative luminance of `#rrggbb`."""
    parts = [int(colour[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in parts]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(first: str, second: str) -> float:
    """WCAG contrast ratio of two `#rrggbb` colours."""
    high, low = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


@pytest.mark.parametrize("dark", [False, True], ids=["light", "dark"])
def test_every_text_colour_reads_on_its_background(*, dark: bool) -> None:
    """Each text/background pair of the theme reaches 4.5:1."""
    colours = _theme(dark=dark)
    weak = {
        f"{text} on {back}: {contrast(colours[text], colours[back]):.2f}"
        for text, back in PAIRS
        if contrast(colours[text], colours[back]) < _MIN
    }
    assert not weak


def test_wcag_function_knows_black_on_white() -> None:
    """The helper itself: 21:1, symmetric."""
    assert round(contrast("#000000", "#ffffff")) == 21
    assert contrast("#ffffff", "#000000") == contrast("#000000", "#ffffff")


def test_the_theme_rings_what_tab_reaches() -> None:
    """A `:focus-visible` outline for every control; the tiles redraw theirs."""
    theme = (_TEMPLATES / "theme.css.j2").read_text("utf-8")
    assert re.search(
        r"(?m)^:focus-visible\s*\{\s*outline:\s*3px solid var\(--mh-focus\)", theme
    )
    grid = (_TEMPLATES / "pick_grid.css.j2").read_text("utf-8")
    assert ".file:focus-visible" in grid


def test_reduced_motion_cuts_every_transition_and_animation() -> None:
    """The shared theme caps all durations (the slideshow's cross-fade included)."""
    theme = (_TEMPLATES / "theme.css.j2").read_text("utf-8")
    rule = theme[theme.index("@media (prefers-reduced-motion: reduce)") :]
    assert "*, *::before, *::after" in rule
    assert "animation-duration: .01ms !important" in rule
    assert "transition-duration: .01ms !important" in rule


@pytest.mark.parametrize("template", ["quarantine.html.j2", "people.html.j2"])
def test_a_framed_page_carries_the_shared_comfort(template: str) -> None:
    """The rendered page includes the rule: no page needs its own."""
    html = render_page(template)
    assert "prefers-reduced-motion: reduce" in html
    assert ":focus-visible" in html
