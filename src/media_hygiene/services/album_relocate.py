"""Album link folders follow a changed `[album] root` (0582).

For each album of `albums.json` whose folder is still in the old root: a journaled
album run makes it again in the new root, then empties the old folder of the links
the journals prove an album run made (`actions/album_vacate`), its marker, and the
folder once empty. A file the journals do not list stays, said. `undo` of the run
puts the old links back and removes the new ones.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.album import AlbumExecutor
from media_hygiene.actions.album_vacate import AlbumVacate, Vacated
from media_hygiene.actions.journal import done_states, journal_file, read_journal
from media_hygiene.actions.kinds import ActionKind, Phase
from media_hygiene.actions.outcome import Tally
from media_hygiene.actions.runs import list_run_ids
from media_hygiene.classify.album_rows import Criteria
from media_hygiene.constants import ALBUM_MARKER
from media_hygiene.services.album import AlbumRequest, AlbumService
from media_hygiene.services.albums import album_store
from media_hygiene.services.journaled_run import new_run
from media_hygiene.services.run_listings import forget_run_listings

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.album import AlbumPrepared
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class Relocated:
    """One album made again in the new root, and what its old folder kept."""

    album: str
    run_id: str
    linked: int
    vacated: Vacated | None  # None: stopped before the old folder was emptied


def albums_in(runtime: Runtime, old_root: Path) -> tuple[str, ...]:
    """The albums of `albums.json` that still have a folder in the old root.

    Args:
        runtime: Settings, mount points and output.
        old_root: The old root (container path).

    Returns:
        Their names, as saved.
    """
    shelf = album_store(runtime).on_disk()
    return tuple(a.name for a in shelf.albums.albums if (old_root / a.name).is_dir())


def made_in(journal_dir: Path, folder: Path) -> dict[Path, Path]:
    """The links album runs made in a folder, each with its photo.

    Args:
        journal_dir: The journals.
        folder: The album folder (container path).

    Returns:
        Each link and the photo it was made from (the latest run wins).
    """
    made: dict[Path, Path] = {}
    for run_id in reversed(list_run_ids(journal_dir)):  # oldest first
        entries = read_journal(journal_file(journal_dir, run_id))
        for entry in done_states(entries, Phase.ALBUM):
            link = Path(entry.path)
            if (
                entry.action is ActionKind.LINK
                and entry.keeper
                and link.parent == folder
            ):
                made[link] = Path(entry.keeper)
    return made


@dataclass(frozen=True, slots=True)
class AlbumMove:
    """What a move needs: the runtime (holding the new root), progress, Ctrl+C."""

    runtime: Runtime
    progress: ProgressSink
    stop: Callable[[], bool]


def _moved(
    move: AlbumMove, prepared: AlbumPrepared, leaving: tuple[Path, bool]
) -> Relocated:
    """Make one album again in the new root, then empty its old folder.

    Args:
        move: The runtime, progress, Ctrl+C.
        prepared: The album, in the new root.
        leaving: Its old folder; whether it is the last of the old root, which is
            left then (0626).

    Returns:
        What became of it.
    """
    old, last = leaving
    made = made_in(move.runtime.locations.journal_dir, old)
    folder = prepared.plan.folder
    tally = Tally()
    with new_run(move.runtime, move.progress, Phase.ALBUM) as context:
        executor = AlbumExecutor(context, tally)
        ended = executor.run(prepared.plan, move.stop)
        vacated = None
        if not (ended.interrupted or ended.unsupported):
            vacate = AlbumVacate(executor.changes, tally)
            vacated = vacate.run(old, made, folder / ALBUM_MARKER)
            if last and vacated.folder_removed:
                strays = vacate.leave_root(old.parent, folder.parent)
                vacated = replace(vacated, kept=strays)
    run_id = context.quarantine_run_dir.name
    forget_run_listings(move.runtime, run_id, Phase.ALBUM)
    return Relocated(folder.name, run_id, tally.done, vacated)


def relocate(move: AlbumMove, old_root: Path) -> tuple[Relocated, ...]:
    """Make each album of the old root again in the new one, then empty the old.

    Args:
        move: The runtime whose settings name the new root, progress, Ctrl+C.
        old_root: The old root (container path).

    Returns:
        One result per album moved, in `albums.json` order.
    """
    service = AlbumService(move.runtime, move.progress)
    service.ensure_ready()
    done: list[Relocated] = []
    names = albums_in(move.runtime, old_root)
    for name in names:
        if move.stop():
            break
        prepared = service.prepare(AlbumRequest(name, Criteria()))
        old = old_root / name
        if prepared.plan.folder != old:
            done.append(_moved(move, prepared, (old, name == names[-1])))
    return tuple(done)
