"""No two scripts of a page declare the same top-level name.

The classic `<script>` blocks of a page share one global scope: a second top-level
`const`/`let`/`class` of a name already declared (by `let`, `const`, `class` or
`function`) is a SyntaxError, and the browser drops that whole block (the library
page's `asked`, found by its browser walk, 2026-11-11). Every page `page_render`
renders is read.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Final

import pytest

from media_hygiene.review.page_header import PAGE_STEPS
from tests.support.page_render import render_page

_SCRIPT: Final = re.compile(
    r"<script(?P<attrs>[^>]*)>(?P<body>.*?)</script>", re.DOTALL
)
_DECLARED: Final = re.compile(
    r"(?:^|[;\n}])\s*(?:async\s+)?(?P<kind>const|let|class|function\*?)\s+"
    r"(?P<name>[A-Za-z_$][\w$]*)"
)
_LEXICAL: Final = frozenset({"const", "let", "class"})


def _skip_quoted(code: str, start: int) -> int:
    """The index after the string, template literal or comment opening at `start`."""
    opener = code[start]
    if code.startswith("//", start):
        end = code.find("\n", start)
        return len(code) if end < 0 else end
    if code.startswith("/*", start):
        return code.index("*/", start + 2) + 2
    index = start + 1
    while index < len(code) and code[index] != opener:
        index += 2 if code[index] == "\\" else 1
    return index + 1


def _top_level(code: str) -> str:
    """The code outside any brace, strings and comments blanked."""
    kept: list[str] = []
    depth = 0
    index = 0
    while index < len(code):
        char = code[index]
        if char in "\"'`" or code.startswith(("//", "/*"), index):
            index = _skip_quoted(code, index)
            kept.append(" ")
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
        if depth == 0 or (depth == 1 and char == "{"):
            kept.append(char)
        index += 1
    return "".join(kept)


def _declarations(page: str) -> list[tuple[str, str]]:
    """Every top-level declaration of the page's classic scripts: (kind, name)."""
    found: list[tuple[str, str]] = []
    for script in _SCRIPT.finditer(page):
        attrs = script["attrs"]
        if "src=" in attrs or "module" in attrs or "json" in attrs:
            continue
        found.extend(
            (match["kind"].rstrip("*"), match["name"])
            for match in _DECLARED.finditer(_top_level(script["body"]))
        )
    return found


@pytest.mark.parametrize("template", sorted(PAGE_STEPS))
def test_no_two_scripts_declare_the_same_name(template: str) -> None:
    """A lexical name is declared once on the page, by any kind of declaration."""
    declared = _declarations(render_page(template))
    lexical = {name for kind, name in declared if kind in _LEXICAL}
    counts = Counter(name for _, name in declared)
    clashes = sorted(name for name in lexical if counts[name] > 1)
    assert clashes == []


def test_a_clash_is_found() -> None:
    """The check sees a `const` repeating a `let` of another block, not a nested one."""
    page = (
        "<script>let asked = {}; function f() { const inner = 1; }</script>"
        '<script>const asked = "x"; if (y) { let inner = 2; }</script>'
    )
    names = [name for _, name in _declarations(page)]
    assert names.count("asked") == 2
    assert "inner" not in names


_SHARED: Final = ("mhSay", "mhBusy", "mhPlaceholders", "mhAsk")


@pytest.mark.parametrize("template", sorted(PAGE_STEPS))
def test_the_shared_helpers_are_defined_before_any_script_uses_them(
    template: str,
) -> None:
    """`mhSay`, `mhBusy`, `mhPlaceholders`, `mhAsk` exist before a page script runs.

    The library page called `mhPlaceholders` at load, before the frame had it (0664).
    """
    late: list[str] = []
    defined: set[str] = set()
    for script in _SCRIPT.finditer(render_page(template)):
        body = script["body"]
        late.extend(
            name
            for name in _SHARED
            if name not in defined
            and f"window.{name}(" in body
            and f"window.{name} =" not in body
        )
        defined.update(name for name in _SHARED if f"window.{name} =" in body)
    assert not late, late
