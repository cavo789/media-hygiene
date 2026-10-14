"""What the index knew of the files a clean set aside, until `undo` or `purge` (0156).

A file moved to the quarantine leaves every table (no reader of the index sees it
any more), but its rows are parked here, one JSON document per file, under its run.
`undo` puts them back at the original path: the restored file is not checked,
fingerprinted, described nor analysed for faces again. `purge` drops them with the
quarantine of the run. Version 12 of the index.
"""

from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING, Final

from media_hygiene.index.schema_tables import FORGET, PATH_TABLES

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Sequence

CREATE_PARKED: Final = """
CREATE TABLE IF NOT EXISTS parked (
    path TEXT PRIMARY KEY,
    run TEXT NOT NULL,
    rows TEXT NOT NULL
)
"""
_BYTES: Final = "base64:"  # a BLOB (a face's vector) in the JSON document
_PARK: Final = "INSERT OR REPLACE INTO parked (path, run, rows) VALUES (?, ?, ?)"
_PARKED: Final = "SELECT rows FROM parked WHERE path = ?"
_UNPARK: Final = "DELETE FROM parked WHERE path = ?"
_PURGE: Final = "DELETE FROM parked WHERE run = ?"


def park(
    connection: sqlite3.Connection, run: str, moves: Sequence[tuple[str, str]]
) -> None:
    """Take the rows of each file set aside out of the tables, keeping them aside.

    Args:
        connection: The index.
        run: The run that set them aside.
        moves: Original path and quarantine path of each file.
    """
    for original, quarantined in moves:
        document: dict[str, list[dict[str, object]]] = {}
        for table in PATH_TABLES:
            cursor = connection.execute(
                f"SELECT * FROM {table} WHERE path = ?",  # noqa: S608 - fixed names
                (original,),
            )
            names = [column[0] for column in cursor.description]
            rows = [dict(zip(names, map(_out, row), strict=True)) for row in cursor]
            if rows:
                document[table] = rows
            connection.execute(FORGET[PATH_TABLES.index(table)], (original,))
        if document:
            connection.execute(_PARK, (quarantined, run, json.dumps(document)))


def unpark(connection: sqlite3.Connection, moves: Sequence[tuple[str, str]]) -> int:
    """Put the parked rows of restored files back, at their original path.

    Args:
        connection: The index.
        moves: Quarantine path and original path of each file restored.

    Returns:
        How many files got their rows back.
    """
    restored = 0
    for quarantined, original in moves:
        found = connection.execute(_PARKED, (quarantined,)).fetchone()
        if found is None:
            continue
        for table, rows in json.loads(found[0]).items():
            if table not in PATH_TABLES:
                continue
            for row in rows:
                values = {key: _in(value) for key, value in row.items()}
                values["path"] = original
                columns = ", ".join(values)
                marks = ", ".join("?" for _ in values)
                insert = (
                    f"INSERT OR REPLACE INTO {table} ({columns})"  # noqa: S608 - ours
                    f" VALUES ({marks})"
                )
                connection.execute(insert, tuple(values.values()))
        connection.execute(_UNPARK, (quarantined,))
        restored += 1
    return restored


def forget_runs(connection: sqlite3.Connection, runs: Sequence[str]) -> None:
    """Drop the parked rows of runs whose quarantine was erased (`purge`).

    Args:
        connection: The index.
        runs: The runs purged.
    """
    connection.executemany(_PURGE, [(run,) for run in runs])


def _out(value: object) -> object:
    """A column value as JSON holds it.

    Args:
        value: From SQLite.

    Returns:
        The value; bytes as base64 text.
    """
    if isinstance(value, bytes):
        return _BYTES + base64.b64encode(value).decode("ascii")
    return value


def _in(value: object) -> object:
    """A value of the JSON document as SQLite takes it.

    Args:
        value: From the document.

    Returns:
        The value; base64 text back to bytes.
    """
    if isinstance(value, str) and value.startswith(_BYTES):
        return base64.b64decode(value.removeprefix(_BYTES))
    return value
