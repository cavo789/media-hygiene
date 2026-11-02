"""The folders `config.toml` names that a `sort` emptied or removed (0382).

`[folders] preferred` names folders, not photos: it is not rewritten (the photos may
now lie in several folders). The ones a run took every file out of are said, one line
each, with what to do. The folders placed on the map (`[[places.folders]]`) follow
their photos, or are removed (`sort_links_spots`, 0549). Protected folders and backups
are never touched.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.paths.host_paths import is_within
from media_hygiene.services.sort_links_spots import followed_spots

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping

    from media_hygiene.services.runtime import Runtime


def emptied_settings(runtime: Runtime, moves: Mapping[str, str]) -> tuple[str, ...]:
    """Say which folders of the settings the moves left empty or removed.

    Args:
        runtime: Settings, mount points and output.
        moves: New container path by old one.

    Returns:
        One line per folder.
    """
    settings, mapper = runtime.settings, runtime.mapper
    named = tuple(
        ("[folders] preferred", folder) for folder in settings.folders.preferred
    )
    sources = [Path(old).parent for old in moves]
    lines = []
    for setting, folder in named:
        inside = mapper.to_container(folder)
        if not any(is_within(source, inside) for source in sources):
            continue
        if not _holds_files(inside):
            lines.append(
                _(
                    "{setting} names {folder}, which this run emptied: point it to "
                    "the photos' new folder in config.toml, or remove it."
                ).format(setting=setting, folder=folder)
            )
    return (*lines, *followed_spots(runtime, moves, _holds_files))


def _holds_files(folder: Path) -> bool:
    """Tell whether a folder still holds a file, at any depth.

    Args:
        folder: In the container.

    Returns:
        True at the first file found; False when it is empty or gone.
    """
    return next(_files(folder), None) is not None


def _files(folder: Path) -> Iterator[Path]:
    """The files of a folder, lazily.

    Args:
        folder: In the container.

    Yields:
        Each file.
    """
    if not folder.is_dir():
        return
    yield from (path for path in folder.rglob("*") if path.is_file())
