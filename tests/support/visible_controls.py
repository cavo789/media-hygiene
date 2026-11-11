"""Count the controls a page shows at load, from its HTML (0665).

Present is not visible. A control is a `button`, an `input` (but `type="hidden"`), a
`select`, a `textarea` or a `summary`. It is not counted inside a closed `<details>`
(its own `summary` is), under an element marked `hidden`, inside a `<dialog>` or a
`<template>`. The bar's `#acting`, `#lead` and `#applyNow` carry `hidden` but are shown
greyed by `pick_bar.css.j2`: counted. What scripts add after the load (chips, cards) is
not in the HTML: the CI browser walk counts the page for real.
"""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Final, override

_CONTROLS: Final = frozenset({"button", "input", "select", "textarea", "summary"})
_VOID: Final = frozenset(
    {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta"}
    | {"source", "track", "wbr"}
)
_SHOWN_ANYWAY: Final = frozenset({"acting", "lead", "applyNow"})
_SKIPPED: Final = frozenset({"dialog", "template", "script", "style"})


class _Counter(HTMLParser):
    """Walks the page keeping, per open element, whether it hides what it holds."""

    def __init__(self) -> None:
        super().__init__()
        self.stack: list[tuple[str, bool]] = []  # tag, hides what it holds
        self.count = 0

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        named = dict(attrs)
        marked = "hidden" in named and named.get("id") not in _SHOWN_ANYWAY
        above = [hides for _, hides in self.stack]
        # A closed <details> hides all it holds but its own summary.
        parent_closed = bool(self.stack) and self.stack[-1][0] == "details:closed"
        hidden_above = (
            any(above[:-1]) if tag == "summary" and parent_closed else any(above)
        )
        if tag in _CONTROLS and named.get("type") != "hidden":
            self.count += not (marked or hidden_above)
        if tag in _VOID:
            return
        closed = tag == "details" and "open" not in named
        name = "details:closed" if closed else tag
        self.stack.append((name, marked or closed or tag in _SKIPPED))

    @override
    def handle_endtag(self, tag: str) -> None:
        for at in range(len(self.stack) - 1, -1, -1):
            if self.stack[at][0].split(":")[0] == tag:
                del self.stack[at:]
                return


def visible_controls(page: str) -> int:
    """The controls shown at load without opening anything.

    Args:
        page: The HTML of the page, as served.

    Returns:
        How many controls are visible.
    """
    counter = _Counter()
    counter.feed(page)
    return counter.count
