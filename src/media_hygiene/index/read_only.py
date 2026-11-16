"""Open the index file read-only: no upgrade, no journal file, even on a `:ro` cache."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from pathlib import Path

_READ_ONLY: Final = "?mode=ro"


def connect_read_only(index_file: Path) -> sqlite3.Connection:
    """Open an index file without the right to change it.

    Args:
        index_file: The index.

    Returns:
        The connection, to close after use.

    Raises:
        sqlite3.Error: The file cannot be opened.
    """
    uri = f"{index_file.resolve().as_uri()}{_READ_ONLY}"
    # A page answers in a thread beside its event loop (2026-11-15); SQLite is built
    # serialized (`sqlite3.threadsafety == 3`): one connection may serve any thread.
    return sqlite3.connect(uri, uri=True, check_same_thread=False)
