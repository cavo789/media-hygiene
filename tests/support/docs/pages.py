"""Refresh the console outputs of the documentation, in place, from fresh captures.

A generated block is announced by an HTML comment, invisible on GitHub:

    <!-- capture: clean.txt|re:^1 |❓ -->
    ```text
    …
    ```

The specification names a capture, optionally followed by `|START|END`: the lines from
the first one containing START (`re:` for a regular expression) to the next one
containing END. END may be empty (to the end), `<blank>` (to the next empty line) or `.`
(that line only); the lines the terminal wrapped after the END line come with it.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

_BLOCK: Final = re.compile(
    r"^(?P<head><!-- capture: (?P<spec>.+?) -->\n```\w*\n)(?P<body>.*?)^```$",
    re.MULTILINE | re.DOTALL,
)
_REGEX: Final = "re:"
_TO_END: Final = ""
_TO_BLANK: Final = "<blank>"
_SAME_LINE: Final = "."
# A line ending a sentence is complete; after any other line, a line that does not start
# like a new message continues it, wrapped by the terminal.
_SENTENCE_ENDS: Final = (".", ":", "?", "!")
_STARTERS: Final = (
    "💡",
    "✅",
    "❓",
    "⚠",
    "•",
    "─",
    "│",
    "┌",
    "└",
    "┏",
    "┃",
    "┡",
    "┗",
    "╭",
    "╰",
)
# The Czkawka command the audit prints is one very long line: the docs shorten it.
_CZKAWKA: Final = re.compile(
    r"^(docker run --rm -v \"[^\"]+\").*( -C /out/czkawka\.json)$"
)


def _start(lines: list[str], bound: str) -> int:
    """The first line matching a START bound."""
    if bound.startswith(_REGEX):
        pattern = re.compile(bound.removeprefix(_REGEX))
        return next(index for index, line in enumerate(lines) if pattern.search(line))
    return next(index for index, line in enumerate(lines) if bound in line)


def _last(lines: list[str], start: int, bound: str) -> int:
    """The line an END bound points at."""
    if bound == _SAME_LINE:
        return start
    after = enumerate(lines[start + 1 :], start=start + 1)
    if bound == _TO_BLANK:
        return next(index for index, line in after if not line) - 1
    return next(index for index, line in after if bound in line)


def _end(lines: list[str], start: int, bound: str) -> int:
    """The last line of an excerpt: the END line, and what wraps after it."""
    if bound == _TO_END:
        return len(lines) - 1
    end = _last(lines, start, bound)
    while end + 1 < len(lines) and lines[end + 1].strip():
        finished = lines[end].endswith(_SENTENCE_ENDS)
        if finished or lines[end + 1].lstrip().startswith(_STARTERS):
            break
        end += 1
    return end


def excerpt(captures: Mapping[str, str], spec: str) -> str:
    """Cut the lines a specification asks for out of a capture.

    Args:
        captures: The fresh captures, by name.
        spec: `name` or `name|START|END`.

    Returns:
        The lines, without trailing empty ones.

    Raises:
        KeyError: The specification names an unknown capture.
    """
    name, *bounds = spec.split("|")
    if name not in captures:
        message = f"unknown capture {name!r} in {spec!r}"
        raise KeyError(message)
    lines = captures[name].splitlines()
    if bounds:
        start = _start(lines, bounds[0])
        lines = lines[
            start : _end(lines, start, bounds[1] if len(bounds) > 1 else "") + 1
        ]
    lines = [_CZKAWKA.sub(r"\1 …\2", line) for line in lines]
    return "\n".join(lines).strip("\n")


def refresh(page: Path, captures: Mapping[str, str]) -> None:
    """Replace every generated block of a page with its fresh capture.

    Args:
        page: A Markdown page of the documentation.
        captures: The fresh captures, by name.
    """
    text = page.read_text(encoding="utf-8")
    fresh = _BLOCK.sub(
        lambda block: f"{block['head']}{excerpt(captures, block['spec'])}\n```", text
    )
    page.write_text(fresh, encoding="utf-8")


def specifications(page: Path) -> list[str]:
    """The capture specifications a page uses.

    Args:
        page: A Markdown page of the documentation.

    Returns:
        Its specifications, in order.
    """
    return [
        block["spec"] for block in _BLOCK.finditer(page.read_text(encoding="utf-8"))
    ]
