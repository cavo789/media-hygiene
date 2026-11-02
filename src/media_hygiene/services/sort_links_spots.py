"""After `sort` or a move: the `[[places.folders]]` of a folder the run emptied (0549).

The tool knows the folder is gone, so the user is not asked to edit `config.toml`:
when every photo of the folder went to one new folder, the place follows them there;
else the entry is removed and kept in the cache (`places-folders-removed.json`), so
that the run's `undo`, which brings the photos back, writes it again. Each change is
read back from the disk.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.config.places_settings import FolderPosition
from media_hygiene.i18n import _
from media_hygiene.paths.host_paths import is_within
from media_hygiene.places.config_folders import read_folders, save_folders

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from media_hygiene.services.runtime import Runtime

REMOVED_FILE: Final = "places-folders-removed.json"


@dataclass(frozen=True, slots=True)
class _Pass:
    """What one run changes: the positions to write, the lines to say."""

    runtime: Runtime
    moves: Mapping[str, str]
    holds_files: Callable[[Path], bool]
    changes: list[FolderPosition | str] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)


def followed_spots(
    runtime: Runtime, moves: Mapping[str, str], holds_files: Callable[[Path], bool]
) -> tuple[str, ...]:
    """Move, remove or restore the folder positions the moves concern.

    Args:
        runtime: Settings, mount points and output.
        moves: New container path by old one.
        holds_files: Whether a container folder still holds a file.

    Returns:
        One line per position changed, read back from `config.toml`.
    """
    config_file = runtime.locations.config_file
    removed_file = runtime.locations.cache_dir / REMOVED_FILE
    removed = _removed(removed_file)
    spots = read_folders(config_file) if config_file.is_file() else ()
    run = _Pass(runtime, moves, holds_files)
    for spot in spots:
        _follow(run, spot, removed)
    known = {spot.folder.casefold() for spot in spots}
    for key, spot in list(removed.items()):
        if key not in known and _restore(run, spot):
            del removed[key]
    if not run.changes:
        return ()
    save_folders(config_file, run.changes)
    _keep(removed_file, removed)
    return _read_back(config_file, run.lines)


def _follow(
    run: _Pass, spot: FolderPosition, removed: dict[str, FolderPosition]
) -> None:
    """Move a position after its photos, or remove it, when the run emptied its folder.

    Args:
        run: The run's moves and changes.
        spot: A position of `config.toml`.
        removed: The positions waiting for an undo, completed.
    """
    mapper = run.runtime.mapper
    inside = mapper.to_container(spot.folder)
    targets = {
        Path(new).parent
        for old, new in run.moves.items()
        if is_within(Path(old), inside)
    }
    if not targets or run.holds_files(inside):
        return
    run.changes.append(spot.folder)
    if len(targets) == 1:
        target = mapper.to_host(targets.pop())
        run.changes.append(spot.model_copy(update={"folder": target}))
        run.lines.append(
            _("Place of {folder} moved to {target}, with its photos.").format(
                folder=spot.folder, target=target
            )
        )
        return
    removed[spot.folder.casefold()] = spot
    run.lines.append(
        _(
            "Place of {folder} removed from config.toml: its photos went to "
            "several folders."
        ).format(folder=spot.folder)
    )


def _restore(run: _Pass, spot: FolderPosition) -> bool:
    """Write a removed position again when the run brought photos back into its folder.

    Args:
        run: The run's moves and changes.
        spot: A position removed by an earlier run.

    Returns:
        True when it is written back.
    """
    inside = run.runtime.mapper.to_container(spot.folder)
    back = any(is_within(Path(new), inside) for new in run.moves.values())
    if not back or not run.holds_files(inside):
        return False
    run.changes.append(spot)
    run.lines.append(
        _("Place of {folder} written back in config.toml.").format(folder=spot.folder)
    )
    return True


def _read_back(config_file: Path, lines: list[str]) -> tuple[str, ...]:
    """Prove the write by reading the file again.

    Args:
        config_file: `config.toml`.
        lines: What was changed.

    Returns:
        The lines, with how many positions the file now holds.
    """
    count = len(read_folders(config_file))
    said = _("config.toml read back: {count} folder positions.").format(count=count)
    return (*lines, said)


def _removed(path: Path) -> dict[str, FolderPosition]:
    """The positions removed by earlier runs, waiting for an undo.

    Args:
        path: The cache file; missing or unreadable: none.

    Returns:
        Them, by folder in lower case.
    """
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
        spots = [FolderPosition.model_validate(row) for row in rows]
    except OSError, ValueError, TypeError:
        return {}
    return {spot.folder.casefold(): spot for spot in spots}


def _keep(path: Path, removed: Mapping[str, FolderPosition]) -> None:
    """Write the positions waiting for an undo, atomically.

    Args:
        path: The cache file.
        removed: Them.
    """
    text = json.dumps(
        [spot.model_dump() for spot in removed.values()], ensure_ascii=False, indent=1
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)
