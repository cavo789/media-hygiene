"""`undo --pick` (0525): the quarantine as tiles, and the photos picked put back.

Every run's journal says which files it set aside and where: those still in a
quarantine are listed, newest run first. *Restore* is a partial undo of each run
concerned (`undo_pick`), with the guards of `undo` (a drive's quarantine not mounted
refuses its run); what is shown afterwards is read again from the disk.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.actions.journal import journal_file, read_journal
from media_hygiene.actions.outcome import combine
from media_hygiene.actions.runs import list_run_ids
from media_hygiene.actions.undo_pick import RunPick, quarantined_now
from media_hygiene.console.formatting import human_size
from media_hygiene.constants import VIDEO_EXTENSIONS
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.near_views import folder_and_name
from media_hygiene.review.views import ORIGINAL_LINK, PREVIEW_LINK
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.disk_only import only_by_run
from media_hygiene.services.undo import undo_pick
from media_hygiene.services.undo_guard import ensure_undo_ready

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.actions.journal import JournalEntry
    from media_hygiene.services.runtime import Runtime

_FROZEN: Final = ConfigDict(frozen=True, extra="forbid")
_KEY_SEPARATOR: Final = "~"  # never in a run identifier, safe in a URL


class QuarantinedTile(BaseModel):
    """One file of the quarantine, as the page shows it."""

    model_config = _FROZEN

    key: str
    run: str
    name: str
    folder: str  # where it comes back, as Windows names it
    size: str
    video: bool
    preview: str
    original: str


class QuarantineState(BaseModel):
    """`GET /api/state`: the files of every quarantine, newest run first."""

    model_config = _FROZEN

    tiles: tuple[QuarantinedTile, ...]
    only: dict[str, int] | None = None  # per run, nowhere else (0782); None: unknown


class Restored(BaseModel):
    """`POST /api/restore`: what came back, read back from the disk, and what not."""

    model_config = _FROZEN

    back: tuple[str, ...]  # the host paths now on the disk
    left: tuple[str, ...]  # why the others stayed: "<path>: <reason>"
    state: QuarantineState


def tile_key(run_id: str, seq: int) -> str:
    """The key of one quarantined file: its run and its action.

    Args:
        run_id: The run.
        seq: The action's sequence number.

    Returns:
        The key, e.g. `20261103-101500~7`.
    """
    return f"{run_id}{_KEY_SEPARATOR}{seq}"


def quarantined(runtime: Runtime) -> dict[str, JournalEntry]:
    """Every file still in a quarantine, by key, newest run first.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The journal line of each; empty without a persistent journal.
    """
    if not runtime.persistent(MountKind.JOURNAL):
        return {}
    journal_dir = runtime.locations.journal_dir
    return {
        tile_key(run_id, entry.seq): entry
        for run_id in list_run_ids(journal_dir)
        for entry in quarantined_now(read_journal(journal_file(journal_dir, run_id)))
    }


def quarantine_state(runtime: Runtime) -> QuarantineState:
    """Describe the quarantine for the page, read from the journals and the disk.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        Its tiles.
    """
    tiles = []
    for key, entry in quarantined(runtime).items():
        folder, name = folder_and_name(entry.host_path)
        suffix = Path(entry.path).suffix.lower()
        tiles.append(
            QuarantinedTile(
                key=key,
                run=key.split(_KEY_SEPARATOR, 1)[0],
                name=name,
                folder=folder,
                size=human_size(entry.size),
                video=suffix in VIDEO_EXTENSIONS,
                preview=f"{PREVIEW_LINK}{key}.jpg",
                original=f"{ORIGINAL_LINK}{key}{suffix}",
            )
        )
    runs = list(dict.fromkeys(tile.run for tile in tiles))
    return QuarantineState(tiles=tuple(tiles), only=only_by_run(runtime, runs))


def restore_picked(runtime: Runtime, keys: Iterable[str]) -> Restored:
    """Put the files picked back where they were: a partial undo of each run.

    Args:
        runtime: Settings, mount points and output.
        keys: The tiles picked; a key no longer in the quarantine is ignored.

    Returns:
        The files back, read from the disk, the others with their reason, and the
        quarantine as it is now.

    Raises:
        MountError: A run's quarantine is not mounted, or `undo` cannot act here;
            nothing was changed.
    """
    known = quarantined(runtime)
    by_run: dict[str, set[int]] = defaultdict(set)
    for key in keys:
        if key in known:
            by_run[key.split(_KEY_SEPARATOR, 1)[0]].add(known[key].seq)
    ensure_undo_ready(runtime, sorted(by_run))
    outcome = combine(
        [
            undo_pick(runtime, RunPick(run_id, frozenset(seqs)), NullProgress())
            for run_id, seqs in by_run.items()
        ]
    )
    picked = [known[key] for key in keys if key in known]
    back = tuple(entry.host_path for entry in picked if Path(entry.path).is_file())
    left = tuple(
        f"{incident.path}: {incident.reason}"
        for incident in (*outcome.skipped, *outcome.failed)
    )
    return Restored(back=back, left=left, state=quarantine_state(runtime))


def source_of(runtime: Runtime, key: str) -> Path | None:
    """The quarantined file a tile shows.

    Args:
        runtime: Settings, mount points and output.
        key: The tile's key.

    Returns:
        The file in the quarantine, or None for an unknown key.
    """
    entry = quarantined(runtime).get(key)
    return Path(entry.quarantine) if entry and entry.quarantine else None
