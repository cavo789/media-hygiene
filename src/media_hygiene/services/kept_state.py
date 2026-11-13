"""A page's heavy state kept while the index and `/config` are unchanged (0804).

The map, the people page, the folder tree and *Events found* read the whole index
again at every visit: 1.8 to 3.7 s each at 100,000 files (measured 2026-11-11,
`tests/measure/pages-budget.md`), although nothing changed between two visits. Each
now keeps what it built with the key it was built under, and builds again only when
the key changes:

- the index file: its inode, size, modification and change times (a commit, a file
  replaced by `shrink` or a restore, a copy keeping the mtime, a `touch`), the change
  counter of its header (bumped by every commit in rollback mode, even two within the
  same clock tick), and the same signature of its `-wal` file;
- every file under `/config` but `.history/`: `config.toml`, the people and events
  files (an edit in place, an atomic save, a copy, a `touch`, a file added or removed);
- the settings the page was built with (the CLI's layer, `config.toml` loaded again).

A change saved through a page goes to `/config` or the index, so it is seen at the
next visit without any call. Files moved on the disk by hand, the index not told, are
not part of the key: the pages read the index, and the next audit tells it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.people.people_memo import file_signature

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Callable

    from media_hygiene.services.runtime import Runtime

HISTORY: Final = ".history"  # previous versions of the files: no page reads them
_COUNTER: Final = slice(24, 28)  # SQLite header: file change counter
_HEADER: Final = 28
_WAL: Final = "-wal"
_MAIN_FILE: Final = "SELECT file FROM pragma_database_list WHERE name = 'main'"

type Key = tuple[object, ...]


def index_signature(index_file: Path | None) -> Key:
    """What changes when the index is written or replaced.

    Args:
        index_file: The index; None for one in memory.

    Returns:
        The file's and its `-wal` file's signatures, and its change counter; a key
        equal to no other for an index in memory (nothing is kept).
    """
    if index_file is None:
        return (object(),)
    try:
        with index_file.open("rb") as stream:
            counter = stream.read(_HEADER)[_COUNTER]
    except OSError:
        counter = b""
    wal = index_file.with_name(index_file.name + _WAL)
    return (file_signature(index_file), counter, file_signature(wal))


def connection_file(connection: sqlite3.Connection) -> Path | None:
    """The file an open index reads.

    Args:
        connection: The index.

    Returns:
        Its main database file; None for one in memory.
    """
    row = connection.execute(_MAIN_FILE).fetchone()
    return Path(row[0]) if row is not None and row[0] else None


def config_signature(config_dir: Path) -> Key:
    """What changes when a file of `/config` is written, added or removed.

    Args:
        config_dir: `/config`.

    Returns:
        Each file's path and signature, sorted; `.history/` left out.
    """
    found: list[tuple[str, object]] = []
    for folder, folders, files in os.walk(config_dir):
        folders[:] = [name for name in folders if name != HISTORY]
        found.extend(
            (path, file_signature(Path(path)))
            for path in (os.path.join(folder, name) for name in files)  # noqa: PTH118
        )
    return tuple(sorted(found, key=lambda entry: entry[0]))


def page_key(runtime: Runtime) -> Key:
    """The key of a page built from the index, `/config` and the settings.

    Args:
        runtime: The server's runtime now.

    Returns:
        The index's signature, `/config`'s, the settings.
    """
    locations = runtime.locations
    return (
        index_signature(locations.index_file),
        config_signature(locations.config_dir),
        runtime.settings,
    )


@dataclass(slots=True)
class KeptState[T]:
    """One value, kept with the key it was built under."""

    _key: Key | None = None
    _value: T | None = None
    _builds: int = field(default=0)

    @property
    def builds(self) -> int:
        """How many times the value was built: what the tests count.

        Returns:
            The count.
        """
        return self._builds

    def value(self, key: Callable[[], Key], build: Callable[[], T]) -> T:
        """The value kept, or built again when the key changed.

        The key is read again after the build, so that what the build itself
        writes (the people page's face groups) does not make the next visit
        build again; a change by another process during the build waits for the
        next one.

        Args:
            key: Reads the key now.
            build: Builds the value; an exception keeps nothing.

        Returns:
            The value.
        """
        if self._value is not None and self._key == key():
            return self._value
        self._key, self._value = None, None
        built = build()
        self._key, self._value = key(), built
        self._builds += 1
        return built

    def forget(self) -> None:
        """Build again at the next ask."""
        self._key, self._value = None, None
