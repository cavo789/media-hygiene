"""Folders skipped by name, wherever they are: system, trash and software folders.

Names are globs (`fnmatch`) matching the whole folder name, case ignored. The user's
`[scan] excluded_names` add to the system ones, never replace them.
"""

from __future__ import annotations

from fnmatch import fnmatchcase
from typing import TYPE_CHECKING, Final

from media_hygiene.paths.docker_run import TOOL_HOME

if TYPE_CHECKING:
    from collections.abc import Iterable

# System, trash and thumbnail folders that never hold user media: Windows recycle bin,
# Synology (@eaDir, #recycle), QNAP (@Recycle, .@__thumb), freedesktop trash
# (.Trash-<uid>) and thumbnails, macOS trash on external volumes (.Trashes); and the
# tool's own folder (quarantine, reports, cache), reached when a whole drive or the home
# is given as photos (0192).
SYSTEM_DIR_NAMES: Final = (
    TOOL_HOME,
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
