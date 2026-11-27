"""How many copies the import set aside, kept for its end line (0801).

The copies step (`phone-end --copies`) and the end step run in their own containers:
the count travels in a small file of `/reports` (never `/config`). The end line reads
it once and removes it, so a later import without the step never reads an old count.
"""

from __future__ import annotations

import contextlib
import json
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from pathlib import Path

ASIDE_COUNT: Final = "import-copies-aside.json"
_KEY: Final = "aside"


def remember_aside(reports: Path, count: int) -> None:
    """Keep the number of copies the import set aside, for its end line.

    Args:
        reports: The reports folder.
        count: How many copies were set aside (0 included: it replaces an older one).
    """
    # Unwritable: the end line says nothing of the copies, never a failed import.
    with contextlib.suppress(OSError):
        (reports / ASIDE_COUNT).write_text(json.dumps({_KEY: count}), encoding="utf-8")


def take_aside(reports: Path) -> int:
    """Read the number kept, once, and remove it.

    Args:
        reports: The reports folder.

    Returns:
        The count; 0 without the file or when it cannot be read.
    """
    path = reports / ASIDE_COUNT
    try:
        count = int(json.loads(path.read_text(encoding="utf-8"))[_KEY])
        path.unlink()
    except OSError, ValueError, KeyError, TypeError:
        return 0
    return max(count, 0)
