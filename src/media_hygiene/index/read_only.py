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
    return sqlite3.connect(uri, uri=True)
