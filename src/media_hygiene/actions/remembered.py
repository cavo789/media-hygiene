"""What the journals remember of the files set aside by a choice (0216).

Every journal is read: a file set aside (`ActionKind.remembered`) remembers its
content (size, SHA-256); a later `undo` restoring it forgets it (the user wanted it
back). The last word wins, per content, whatever run said it. `purge` empties the
quarantine of a run, never its journal: a purged run still counts.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Final

from media_hygiene.actions.kinds import REMEMBERED, ActionKind, Phase
from media_hygiene.constants import JOURNAL_SUFFIX
from media_hygiene.index.journal_words import (
    WORDS_VERSION,
    forget_journals,
    keep_words,
    kept_words,
    read_signatures,
)
from media_hygiene.plan.returned import JournalWord, Remembered, RememberedSet

if TYPE_CHECKING:
    import sqlite3
    from pathlib import Path

    from media_hygiene.plan.returned import ContentKey

_LOGGER = logging.getLogger(__name__)
# The line of a `done` action of a kind remembered holds these (pydantic writes no
# space): the others are skipped before parsing, most of a journal being copies.
_DONE: Final = '"status":"done"'
_ACTIONS: Final = tuple(f'"action":"{kind.value}"' for kind in REMEMBERED)


def remembered_set(journal_dir: Path, connection: sqlite3.Connection) -> RememberedSet:
    """Read every journal: the contents set aside by a choice and not restored since.

    Args:
        journal_dir: Journal mount point.
        connection: The index, keeping what each journal said (`journal_words`).

    Returns:
        The contents, by size and SHA-256.
    """
    full: dict[ContentKey, Remembered] = {}
    partial: dict[ContentKey, Remembered] = {}
    for word in sorted(_words(journal_dir, connection), key=lambda word: word.at):
        contents = partial if word.partial else full
        said = word.said
        if said is None:
            contents.pop(word.key, None)
        elif said.action is ActionKind.QUARANTINE_RETURNED and word.key in contents:
            continue  # set aside again: when and why it was first set aside stay
        else:
            contents[word.key] = said
    return RememberedSet(MappingProxyType(full), MappingProxyType(partial))


def _words(journal_dir: Path, connection: sqlite3.Connection) -> list[JournalWord]:
    """List every word of every journal on a content set aside by a choice.

    A journal unchanged since the last audit is not read again: its words are kept
    in the index, under its size and modification time.

    Args:
        journal_dir: Journal mount point.
        connection: The index.

    Returns:
        Each `done` set-aside, and each `done` undo of one.
    """
    journals = sorted(journal_dir.glob(f"*{JOURNAL_SUFFIX}"))
    kept = read_signatures(connection)
    names = {journal.name.removesuffix(JOURNAL_SUFFIX) for journal in journals}
    forget_journals(connection, set(kept) - names)
    words: list[JournalWord] = []
    for journal in journals:
        run_id = journal.name.removesuffix(JOURNAL_SUFFIX)
        try:
            stat = journal.stat()
        except OSError:
            continue
        signature = (stat.st_size, stat.st_mtime_ns, WORDS_VERSION)
        if kept.get(run_id) == signature:
            words += kept_words(connection, run_id)
            continue
        lines = _lines(journal)
        if lines is None:
            continue  # read again next time: never kept as saying nothing
        read = [word for line in lines for word in _read(run_id, line)]
        keep_words(connection, (run_id, signature), read)
        words += read
    return words


def _read(run_id: str, line: str) -> list[JournalWord]:
    """Read one line; nothing when this version cannot.

    Args:
        run_id: The run of the journal.
        line: A `done` line on a kind remembered.

    Returns:
        Its words: by SHA-256, by partial digest, or both.
    """
    try:
        return _word(run_id, json.loads(line))
    except ValueError, KeyError, TypeError:
        _LOGGER.debug("Unreadable line skipped in the journal of %s", run_id)
        return []


def _word(run_id: str, fields: dict[str, Any]) -> list[JournalWord]:
    """Read one `done` line (plain JSON: pydantic is 2 times slower, measured).

    Args:
        run_id: The run of the journal.
        fields: The line, decoded.

    Returns:
        A word per digest it names: its SHA-256, its partial digest (a gone file
        marked deleted, 0224, and the file that matched it).

    Raises:
        TypeError: The size or a digest is of another kind.
    """
    at = datetime.fromisoformat(fields["at"])
    size = fields["size"]
    digests = [(fields.get("sha256"), False), (fields.get("partial"), True)]
    named = [(digest, partial) for digest, partial in digests if digest is not None]
    if not isinstance(size, int) or any(not isinstance(d, str) for d, _p in named):
        raise TypeError(size)
    said = None
    if Phase(fields["phase"]) is not Phase.UNDO:
        action = ActionKind(fields["action"])
        said = Remembered(run_id, at, action, fields["host_path"])
    return [JournalWord(at, (size, d), said, partial=p) for d, p in named]


def _lines(journal: Path) -> list[str] | None:
    """List the `done` lines of a journal on a kind remembered.

    A line this version cannot read (a newer kind, a corrupt line) is skipped: what
    is remembered never stops an audit.

    Args:
        journal: One run's journal.

    Returns:
        The lines, in write order; None when the journal cannot be read.
    """
    try:
        text = journal.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        _LOGGER.warning("Cannot read %s: %s", journal, exc.strerror)
        return None
    return [
        line
        for line in text.splitlines()
        if _DONE in line and any(action in line for action in _ACTIONS)
    ]
