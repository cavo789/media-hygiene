"""The archive of `backup` / `restore` (0352): written, then read back and proven.

One zip: `index.sqlite` (a copy made by SQLite's own `backup`, never a raw copy of a
database that may be open), the files of `/config`, and `manifest.json` (image
version, index schema, SHA-256 of each member, row counts of the costly tables).
Reading one back is `backup_check`.
"""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from pathlib import Path

MANIFEST: Final = "manifest.json"
INDEX_MEMBER: Final = "index.sqlite"
CONFIG_PREFIX: Final = "config/"
FORMAT: Final = 1
# The tables long to rebuild, counted in the manifest and shown (`mh tags`, `people`).
COUNTED: Final = ("files", "tags", "descriptions", "meanings", "faces")
_CHUNK: Final = 1 << 20
_INTACT: Final = "ok"
_COUNT: Final = "SELECT COUNT(*) FROM {table}"  # a name of `COUNTED` only


class BackupError(MediaHygieneError):
    """An archive is missing, damaged, or made by a newer image."""


@dataclass(frozen=True, slots=True)
class Manifest:
    """What an archive says of itself."""

    version: str  # the image that wrote it
    schema: int  # `PRAGMA user_version` of its index
    members: dict[str, str]  # name → SHA-256
    counts: dict[str, int]  # table → rows


def digest(path: Path) -> str:
    """The SHA-256 of a file, read in chunks.

    Args:
        path: The file.

    Returns:
        Its hexadecimal digest.
    """
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(_CHUNK):
            sha.update(chunk)
    return sha.hexdigest()


def copy_index(source: Path, target: Path) -> None:
    """Copy an index with SQLite's `backup`: consistent even while it is open.

    Args:
        source: The live index.
        target: The copy, created.
    """
    with (
        sqlite3.connect(f"{source.resolve().as_uri()}?mode=ro", uri=True) as live,
        sqlite3.connect(target) as copy,
    ):
        live.backup(copy)
    live.close()
    copy.close()


def index_facts(index: Path) -> tuple[int, dict[str, int]]:
    """The schema version and the row counts of an index, after an integrity check.

    Args:
        index: The index file.

    Returns:
        Its `user_version` and the rows of each counted table it has.

    Raises:
        BackupError: The file is not a sound SQLite database.
    """
    connection = sqlite3.connect(f"{index.resolve().as_uri()}?mode=ro", uri=True)
    try:
        (check,) = connection.execute("PRAGMA integrity_check").fetchone()
        if check != _INTACT:
            raise BackupError(
                _("The index of the backup is damaged: {why}.").format(why=check)
            )
        (schema,) = connection.execute("PRAGMA user_version").fetchone()
        names = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        counts = {
            table: int(connection.execute(_COUNT.format(table=table)).fetchone()[0])
            for table in COUNTED
            if table in names
        }
    except sqlite3.DatabaseError as error:
        raise BackupError(
            _("The index of the backup is damaged: {why}.").format(why=error)
        ) from error
    finally:
        connection.close()
    return int(schema), counts
