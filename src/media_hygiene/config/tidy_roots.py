r"""`config tidy`: the root a `path` rule is aimed at, and whether the index covers it.

A pattern such as `(?i)^D:\\Archives\\Trip` names a root (`D:\Archives`); when no
indexed path sits under that root, the index cannot tell whether the rule still
matches: it is left alone, never shown as stale (decided 2026-11-13, TODO 0751). A
pattern naming no root (`(?i)week-end dinant`) is judged as before.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Iterable

_FLAGS: Final = re.compile(r"^(?:\(\?[a-zA-Z]+\))*\^?")
_LITERAL: Final = re.compile(r"(?:\\[\\/.\- ]|[^\\.^$*+?{}\[\]|()])+")
_DRIVE: Final = re.compile(r"^([A-Za-z]:)[\\/]+([^\\/]+)[\\/]")


def aimed_root(pattern: str) -> str | None:
    r"""The drive and first folder a pattern starts with, as a host path.

    Args:
        pattern: The rule's regular expression.

    Returns:
        `X:\\Folder`, casefolded, or None when the pattern names no root.
    """
    rest = _FLAGS.sub("", pattern, count=1)
    literal = _LITERAL.match(rest)
    if literal is None:
        return None
    text = re.sub(r"\\(.)", r"\1", literal.group(0))
    found = _DRIVE.match(text)
    return f"{found[1]}\\{found[2]}".casefold() if found else None


def covered(root: str, paths: Iterable[str]) -> bool:
    """Whether at least one indexed host path sits under the root.

    Args:
        root: The root, as `aimed_root` gives it.
        paths: The indexed host paths.

    Returns:
        True when the index holds a file under it.
    """
    prefix = root + "\\"
    return any(path.replace("/", "\\").casefold().startswith(prefix) for path in paths)
