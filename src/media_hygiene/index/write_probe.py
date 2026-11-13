"""Tell whether another connection is writing the index now (0817).

An audit keeps a write transaction open between its commits (every 5 s), and so does
`people` while it stores faces: SQLite then refuses a second writer at once. Asking
for the write lock without waiting, then giving it back, tells it without changing
anything; no journal file is written (no page is).
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from pathlib import Path

_NO_WAIT: Final = 0.0


def index_busy(index_file: Path) -> bool:
    """Tell whether the index cannot be written now.

    Args:
        index_file: The index.

    Returns:
        True while another connection writes it, or when it cannot be written at
        all (missing, read-only, not an index); False when a writer would go on.
    """
    if not index_file.is_file():
        return True
    try:
        connection = sqlite3.connect(index_file, timeout=_NO_WAIT)
    except sqlite3.Error:
        return True
    try:
        connection.execute("BEGIN IMMEDIATE")
        connection.rollback()
    except sqlite3.Error:
        return True
    finally:
        connection.close()
    return False
