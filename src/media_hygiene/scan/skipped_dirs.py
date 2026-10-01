"""Folders skipped by name, wherever they are: system, trash and software folders.

Names are globs (`fnmatch`) matching the whole folder name, case ignored. The user's
`[scan] excluded_names` add to the system ones, never replace them.
"""

from __future__ import annotations

from fnmatch import fnmatchcase
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Iterable

# System, trash and thumbnail folders that never hold user media: Windows recycle bin,
# Synology (@eaDir, #recycle), QNAP (@Recycle, .@__thumb), freedesktop trash
# (.Trash-<uid>) and thumbnails, macOS trash on external volumes (.Trashes).
SYSTEM_DIR_NAMES: Final = (
    "$recycle.bin",
    "system volume information",
    "@eadir",
    "#recycle",
    "@recycle",
    ".@__thumb",
    ".trash",
    ".trash-*",
    ".trashes",
    ".thumbnails",
)
# Software folders, skipped when other files than media are analysed (paths matter).
APP_DIR_NAMES: Final = frozenset(
    {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "site-packages", "windows"}
    | {"__pycache__", "appdata", "programdata", "program files", "program files (x86)"},
)


def matches_any(name: str, patterns: Iterable[str]) -> bool:
    """Tell whether a folder name matches one of the globs, case ignored.

    Args:
        name: A folder name, e.g. `.Trash-1000`.
        patterns: Globs matching the whole name, e.g. `.trash-*`.

    Returns:
        True when one pattern matches.
    """
    folded = name.casefold()
    return any(fnmatchcase(folded, pattern.casefold()) for pattern in patterns)
