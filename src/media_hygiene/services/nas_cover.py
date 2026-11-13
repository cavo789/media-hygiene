"""The push target's listing kept after a proven push: a NAS copy as cover (0781).

A photo pushed to the NAS, then set aside (a near duplicate, a burst shot), still has
its copy there until the next push moves it into `.removed`. The closing run of a push
(`push_proof`) lists the target anyway: what it found is kept in
`/journal/nas-cover.json` (the journal is the one mount `push` and `clean` require),
by container path with size and date — the same proof `mh push` uses, no content read
over SMB. A file set aside counts as *only on the NAS* when its journal entry has the
same path, size and date there.

What changes it:

- a new proven push replaces it, whatever its target (`--to` elsewhere: the old
  target's copies no longer count, the safe side);
- the next push moves the copy of a file set aside into `.removed`: the listing it
  keeps no longer holds it (`.removed` is never listed, and never counts: it is emptied
  after `[push] keep_removed_days`);
- a purge or an undo takes the file out of the quarantine: nothing asks for its cover.

A copy deleted on the NAS by hand still counts until the next push.
"""

from __future__ import annotations

import contextlib
import json
from dataclasses import dataclass, field
from functools import lru_cache
from typing import TYPE_CHECKING, Final

from media_hygiene.plan.push_entries import Stat

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.actions.journal import JournalEntry

COVER_NAME: Final = "nas-cover.json"


@dataclass(frozen=True, slots=True)
class NasCover:
    """The files the last proven push found in its target, by container path."""

    run_id: str = ""
    target: str = ""  # as Windows writes it
    files: Mapping[str, Stat] = field(default_factory=dict)  # casefolded paths

    def holds(self, entry: JournalEntry) -> bool:
        """Tell whether the target held this file set aside, same size and date.

        Args:
            entry: Its journal entry.

        Returns:
            True when the last push found it there.
        """
        there = self.files.get(entry.path.casefold())
        return there is not None and there.same(Stat(entry.size, entry.mtime_ns))


@dataclass(frozen=True, slots=True)
class Listing:
    """What a proven push keeps: its run, its target, the files found there."""

    run_id: str
    target: str
    files: Mapping[str, Stat]  # by container path


def cover_file(journal_dir: Path) -> Path:
    """Where the listing is kept.

    Args:
        journal_dir: Journal mount point.

    Returns:
        `/journal/nas-cover.json`.
    """
    return journal_dir / COVER_NAME


def keep_cover(journal_dir: Path, listing: Listing) -> None:
    """Replace the kept listing, atomically; a write refused is skipped (no cover).

    Args:
        journal_dir: Journal mount point.
        listing: What the push found.
    """
    file = cover_file(journal_dir)
    said = {
        "run_id": listing.run_id,
        "target": listing.target,
        "files": {
            path.casefold(): [stat.size, stat.mtime_ns]
            for path, stat in sorted(listing.files.items())
        },
    }
    temporary = file.with_name(f".{file.name}.tmp")
    try:
        temporary.write_text(json.dumps(said), "utf-8")
        temporary.replace(file)
    except OSError:
        with contextlib.suppress(OSError):
            file.unlink(missing_ok=True)  # an old listing must not outlive this push


def read_cover(journal_dir: Path) -> NasCover:
    """The listing kept, decoded once per version of the file.

    Args:
        journal_dir: Journal mount point.

    Returns:
        It; empty when no push was proven or the file does not load.
    """
    file = cover_file(journal_dir)
    try:
        stat = file.stat()
    except OSError:
        return NasCover()
    return _decoded(file, (stat.st_ino, stat.st_size, stat.st_mtime_ns))


@lru_cache(maxsize=4)
def _decoded(file: Path, identity: tuple[int, int, int]) -> NasCover:
    """Decode the listing once per identity.

    Args:
        file: The listing.
        identity: Its inode, size and modification time (the cache key).

    Returns:
        It; empty when it does not load.
    """
    del identity  # the key only
    try:
        kept = json.loads(file.read_text("utf-8"))
        files = {str(p): Stat(int(s), int(m)) for p, (s, m) in kept["files"].items()}
        return NasCover(str(kept["run_id"]), str(kept["target"]), files)
    except OSError, ValueError, KeyError, TypeError:
        return NasCover()
