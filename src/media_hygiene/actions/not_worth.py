"""The videos `shrink` found not worth lightening: never tried again while unchanged.

Every journal is read for its `mark-not-worth` lines (`done`); an `undo` of the run
forgets them. A video is known by its path, size and modification time: edited or
replaced, it is tried again.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.kinds import ActionKind, Phase
from media_hygiene.constants import JOURNAL_SUFFIX

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.shrink.candidates import FileKey

_MARK: Final = f'"action":"{ActionKind.MARK_NOT_WORTH.value}"'
_DONE: Final = '"status":"done"'


def not_worth(journal_dir: Path) -> frozenset[FileKey]:
    """Read the videos found not worth it, and not undone since.

    Args:
        journal_dir: Journal mount point.

    Returns:
        Their path, size and modification time.
    """
    said: list[tuple[str, FileKey, bool]] = []
    for journal in sorted(journal_dir.glob(f"*{JOURNAL_SUFFIX}")):
        try:
            lines = journal.read_text(encoding="utf-8").splitlines()
        except OSError, UnicodeDecodeError:
            continue
        said += [
            word
            for line in lines
            if _MARK in line and _DONE in line
            for word in _word(line)
        ]
    kept: set[FileKey] = set()
    for _at, key, undone in sorted(said):
        if undone:
            kept.discard(key)
        else:
            kept.add(key)
    return frozenset(kept)


def _word(line: str) -> list[tuple[str, FileKey, bool]]:
    """Read one mark, or its undo.

    Args:
        line: A `done` line of the mark.

    Returns:
        When it was said, the video, and whether it is an undo; nothing when the
        line cannot be read.
    """
    try:
        fields = json.loads(line)
        key = (str(fields["path"]), int(fields["size"]), int(fields["mtime_ns"]))
        return [(str(fields["at"]), key, fields["phase"] == Phase.UNDO.value)]
    except ValueError, KeyError, TypeError:
        return []
