"""Keep the `path` of the photos given a place current (0551).

The tool's own moves (`sort`, `undo`, the quarantine, *Move to an event*) rewrite it at
once (`follow_place_photos`, from `services.sort_links`); a folder renamed in Explorer
is caught at the end of the next `audit` (`relocate_place_photos`): the id finds the
file, its path is rewritten. Each save is read back; the count is of what reads back.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.config.photo_ref import follow_paths, relocate
from media_hygiene.config.photo_ref_files import rewritten
from media_hygiene.places.config_photos import read_place_photos
from media_hygiene.places.photo_files import save_entries

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.config.photo_ref import PhotoRef

    type Rewrite = Callable[[list[PhotoRef]], list[PhotoRef]]


def follow_place_photos(config_file: Path, moves: Mapping[str, str]) -> int:
    """Rewrite the paths of the photos a run moved.

    Args:
        config_file: `config.toml`; missing: nothing to do.
        moves: New host path by old one.

    Returns:
        The photos whose path changed, counted on the files read back.

    Raises:
        ValueError: A file is not TOML.
        OSError: A file cannot be written.
    """
    return _rewrite(config_file, lambda refs: follow_paths(refs, moves))


def relocate_place_photos(config_file: Path, found: Mapping[str, Sequence[str]]) -> int:
    """Rewrite the paths of the photos renamed outside, found again by id.

    Args:
        config_file: `config.toml`; missing: nothing to do.
        found: The host paths holding each id.

    Returns:
        The photos whose path changed, counted on the files read back.

    Raises:
        ValueError: A file is not TOML.
        OSError: A file cannot be written.
    """
    return _rewrite(config_file, lambda refs: relocate(refs, found))


def _rewrite(config_file: Path, rewrite: Rewrite) -> int:
    """Apply a rewrite to every photo, save when something changed, read back.

    Args:
        config_file: `config.toml`.
        rewrite: The new references, in order, from the old ones.

    Returns:
        The photos whose path changed, counted on the files read back.
    """
    if not config_file.is_file():
        return 0
    before = read_place_photos(config_file)
    after = rewritten(before, rewrite)
    if after is None:
        return 0
    save_entries(config_file, after)
    back = {
        (e.place, p.id): p.path
        for e in read_place_photos(config_file)
        for p in e.photos
    }
    return sum(
        1
        for entry in before
        for photo in entry.photos
        if back.get((entry.place, photo.id), photo.path) != photo.path
    )


def ids_wanted(config_file: Path) -> frozenset[str]:
    """The ids of every photo given a place.

    Args:
        config_file: `config.toml`.

    Returns:
        Them.
    """
    if not config_file.is_file():
        return frozenset()
    return frozenset(p.id for e in read_place_photos(config_file) for p in e.photos)
