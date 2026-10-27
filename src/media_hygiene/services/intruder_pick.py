"""Set intruder files aside: those the user picks, by extension and/or folder (0410).

Never automatic: a docx may matter. The files picked go to the `chosen` key of the
decisions file, as the pages save the files they set aside; `clean --decisions`
then moves them to the quarantine of their drive, journaled, `undo`-able, and skips
one changed or moved since. The folders are walked again when picking (the index
gives the unchanged ones at the cost of a `stat`): what is saved is what lies there
now. Protected and backup folders are left out: they are never changed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.paths.host_paths import is_within
from media_hygiene.scan.intruders import Intruder, outside
from media_hygiene.scan.progress import NullProgress
from media_hygiene.search.chosen import Selection
from media_hygiene.services.chosen_place import chosen_store, reports_ready
from media_hygiene.services.listing import list_media
from media_hygiene.services.policy import backup_folders, keep_policy

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.report.chosen_decisions import ChosenFile
    from media_hygiene.services.runtime import Runtime

FOUND_BY: str = "intruder"  # `found_by` of the files set aside here


@dataclass(frozen=True, slots=True)
class IntruderPick:
    """What the user picked: extensions (`.zip`), folders (container paths), or both.

    Both given: a file must match one of each. None given: nothing is picked.
    """

    extensions: frozenset[str] = frozenset()
    folders: tuple[Path, ...] = ()

    def takes(self, item: Intruder) -> bool:
        """Tell whether a file is picked.

        Args:
            item: An intruder file.

        Returns:
            True when it matches what was picked.
        """
        if not self.extensions and not self.folders:
            return False
        by_extension = not self.extensions or item.extension in self.extensions
        in_folder = not self.folders or any(
            is_within(item.path, folder) for folder in self.folders
        )
        return by_extension and in_folder


def current_intruders(runtime: Runtime) -> tuple[Intruder, ...]:
    """Walk the photo folders now: their intruder files, protected and backups left out.

    Args:
        runtime: Settings, mount points, the index.

    Returns:
        The intruder files, as they are on the disk.
    """
    roots = runtime.mounts.data_roots(runtime.locations.data_dir)
    found = list_media(runtime, roots, NullProgress())
    settings, mapper = runtime.settings, runtime.mapper
    kept_out = (
        *keep_policy(settings, mapper).protected,
        *backup_folders(settings, mapper).folders,
    )
    return outside(found.intruders, kept_out)


def set_intruders_aside(runtime: Runtime, pick: IntruderPick) -> tuple[ChosenFile, ...]:
    """Save the intruder files picked into the decisions file, then read it back.

    Args:
        runtime: Settings, mount points, the index.
        pick: The extensions and folders picked.

    Returns:
        Every file set aside (picked here or on another page), as read back.

    Raises:
        MountError: The reports folder cannot keep the decisions file.
    """
    reports_ready(runtime)
    picked = tuple(
        PhotoVersion(item.path, item.size, item.mtime_ns)
        for item in current_intruders(runtime)
        if pick.takes(item)
    )
    return chosen_store(runtime).add(Selection(picked, FOUND_BY))


def intruders_set_aside(runtime: Runtime) -> tuple[ChosenFile, ...]:
    """The intruder files set aside, as the decisions file holds them now.

    Args:
        runtime: Settings, mount points, the index.

    Returns:
        Them, read from the disk; none without a decisions file.

    Raises:
        DecisionsError: The file is not a decisions file.
    """
    return tuple(
        file for file in chosen_store(runtime).on_disk() if file.found_by == FOUND_BY
    )


def put_intruders_back(runtime: Runtime) -> tuple[ChosenFile, ...]:
    """Take every intruder file out of the decisions file: nothing of them moves.

    Args:
        runtime: Settings, mount points, the index.

    Returns:
        Every file still set aside (by the other pages), as read back.

    Raises:
        MountError: The reports folder cannot keep the decisions file.
    """
    reports_ready(runtime)
    mapper = runtime.mapper
    back = tuple(
        PhotoVersion(mapper.to_container(file.path), file.size, file.mtime_ns)
        for file in intruders_set_aside(runtime)
    )
    return chosen_store(runtime).remove(back)
