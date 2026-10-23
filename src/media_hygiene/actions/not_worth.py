"""The videos `shrink` never tries again while unchanged: not worth it, or its own.

Every journal is read for its `mark-not-worth` lines and the lighter videos it wrote
(`shrunk`), `done`: re-encoding one of those again would lose quality for little (with
a lower `same_crf`, its H.264 may spend more than `bits_per_pixel`: about 0.55 at CRF
18, measured on 2026-10-23). An `undo` of the run forgets them. A video is known by its
path, size and modification time: edited or replaced, it is tried again.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.kinds import ActionKind, Phase
from media_hygiene.constants import JOURNAL_SUFFIX

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.shrink.candidates import FileKey

_MARKS: Final = tuple(
    f'"action":"{kind.value}"'
    for kind in (ActionKind.MARK_NOT_WORTH, ActionKind.SHRUNK)
)
_DONE: Final = '"status":"done"'


def not_worth(journal_dir: Path) -> frozenset[FileKey]:
    """Read the videos found not worth it or written by `shrink`, not undone since.

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
            if _DONE in line and any(mark in line for mark in _MARKS)
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
