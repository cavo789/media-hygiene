"""A check that a script needs no more than ES5: what a 2012 TV browser runs (0291).

Not a full parser: the script is split into tokens (comments and strings left out,
numbers, names, punctuation), then the syntax and the names ES5 does not know are
listed. Enough for the screen page, written by hand without regular expressions.
"""

from __future__ import annotations

import re
from typing import Final

# Comments, strings, then names, numbers and punctuation, longest first.
_TOKEN: Final = re.compile(
    r"""
    (?P<comment>//[^\n]*|/\*.*?\*/)
    |(?P<string>"(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*')
    |(?P<template>`)
    |(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)
    |(?P<number>\d+(?:\.\d+)?)
    |(?P<punct>\.\.\.|=>|\?\?=?|\?\.|\*\*=?|===|!==|[{}()\[\];,.<>+\-*/%&|^!~?:=])
    |(?P<space>\s+)
    |(?P<other>.)
    """,
    re.VERBOSE | re.DOTALL,
)
# Keywords and globals ES5 does not have.
_NAMES: Final = frozenset(
    {"let", "const", "class", "async", "await", "yield", "import", "export", "of"}
    | {"fetch", "Promise", "Symbol", "Map", "Set", "WeakMap", "Reflect", "Proxy"}
)
_PUNCTUATION: Final = frozenset({"=>", "...", "?.", "??", "??=", "**", "**="})


def post_es5(source: str) -> list[str]:
    """List what a script uses beyond ES5.

    Args:
        source: The script.

    Returns:
        Each finding, e.g. `"name let"`, `"punct =>"`, `"template string"`; empty
        when the script is ES5.
    """
    found: list[str] = []
    for match in _TOKEN.finditer(source):
        kind, text = match.lastgroup, match.group()
        if kind == "template":
            found.append("template string")
        elif kind == "name" and text in _NAMES:
            found.append(f"name {text}")
        elif kind == "punct" and text in _PUNCTUATION:
            found.append(f"punct {text}")
        elif kind == "other":
            found.append(f"character {text!r}")
    return found
