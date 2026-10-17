"""What each journal says of the files set aside by a choice, kept by the index (0216).

Reading every journal at each audit takes 0.5 s for 100,000 files set aside
(measured, devcontainer): each journal's words are kept here, under its name, valid
while its size and modification time are those read. A journal grows (a resumed
clean, an `undo`) and is read again; a journal gone takes its words along. Version 15
of the index.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.kinds import ActionKind
from media_hygiene.plan.returned import JournalWord, Remembered

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable, Mapping, Sequence

# What a journal file was when its words were read: its size and modification time,
# and the version of the reading below (`WORDS_VERSION`).
type Signature = tuple[int, int, int]
# Raise it when what is read of a journal changes (a kind remembered, a digest):
# every journal is read again.
WORDS_VERSION: Final = 1

CREATE_JOURNAL_READS: Final = """
CREATE TABLE IF NOT EXISTS journal_reads (
    journal TEXT PRIMARY KEY,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    version INTEGER NOT NULL
)
"""
# `action` and `host_path` are NULL for a restore.
CREATE_JOURNAL_WORDS: Final = """
CREATE TABLE IF NOT EXISTS journal_words (
    journal TEXT NOT NULL,
    at TEXT NOT NULL,
    size INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    action TEXT,
    host_path TEXT,
    partial INTEGER NOT NULL
)
"""
# Every table and index of this module, as `index.schema` creates them.
JOURNAL_TABLES: Final = (
    CREATE_JOURNAL_READS,
    CREATE_JOURNAL_WORDS,
    "CREATE INDEX IF NOT EXISTS journal_words_journal ON journal_words (journal)",
)
_READS: Final = "SELECT journal, size, mtime_ns, version FROM journal_reads"
_WORDS: Final = "SELECT at, size, sha256, action, host_path, partial FROM journal_words"
_OF: Final = f"{_WORDS} WHERE journal = ?"
_FORGET_READ: Final = "DELETE FROM journal_reads WHERE journal = ?"
_FORGET_WORDS: Final = "DELETE FROM journal_words WHERE journal = ?"
_SAVE_READ: Final = (
    "INSERT OR REPLACE INTO journal_reads (journal, size, mtime_ns, version)"
    " VALUES (?, ?, ?, ?)"
)
_SAVE_WORD: Final = (
    "INSERT INTO journal_words (journal, at, size, sha256, action, host_path,"
    " partial) VALUES (?, ?, ?, ?, ?, ?, ?)"
)


def read_signatures(connection: sqlite3.Connection) -> Mapping[str, Signature]:
    """The journals whose words are kept, and what each file was when read.

    Args:
        connection: The index.

    Returns:
        Their signature, by journal name.
    """
    return {
        name: (size, mtime, version)
        for name, size, mtime, version in connection.execute(_READS)
    }


def kept_words(connection: sqlite3.Connection, journal: str) -> list[JournalWord]:
    """The words kept of one journal.

    Args:
        connection: The index.
        journal: The journal's name (its run).

    Returns:
        Them, in no order.
    """
    words: list[JournalWord] = []
    rows = connection.execute(_OF, (journal,))
    for at_text, size, digest, action, host_path, partial in rows:
        at = datetime.fromisoformat(at_text)
        said = None
        if action is not None:
            said = Remembered(journal, at, ActionKind(action), host_path)
        words.append(JournalWord(at, (size, digest), said, partial=bool(partial)))
    return words


def keep_words(
    connection: sqlite3.Connection,
    read: tuple[str, Signature],
    words: Sequence[JournalWord],
) -> None:
    """Keep the words of a journal just read, in place of what was kept of it.

    Args:
        connection: The index.
        read: The journal's name and its signature when read.
        words: What it says.
    """
    journal, signature = read
    forget_journals(connection, (journal,))
    connection.execute(_SAVE_READ, (journal, *signature))
    connection.executemany(
        _SAVE_WORD,
        [
            (
                journal,
                word.at.isoformat(),
                *word.key,
                word.said.action.value if word.said else None,
                word.said.host_path if word.said else None,
                word.partial,
            )
            for word in words
        ],
    )


def forget_journals(connection: sqlite3.Connection, journals: Iterable[str]) -> None:
    """Drop what is kept of journals (gone, or about to be read again).

    Args:
        connection: The index.
        journals: Their names.
    """
    names = [(journal,) for journal in journals]
    connection.executemany(_FORGET_WORDS, names)
    connection.executemany(_FORGET_READ, names)
