"""The files set aside from a page (`search`, `browse`): the `chosen` key, on disk.

Independent of how the files were listed: a selection is a set of file versions
(path, size, modification time) and the search that found them. Each change is saved
at once into the decisions file, its other keys kept, then read back from the disk:
what the page shows is what the file holds, never what was meant to be saved.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.errors import MediaHygieneError
from media_hygiene.report.chosen_decisions import ChosenFile
from media_hygiene.report.decisions import (
    DecisionsFile,
    read_decisions,
    write_decisions,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from media_hygiene.index.descriptions import PhotoVersion
    from media_hygiene.paths.host_paths import HostPathMapper


@dataclass(frozen=True, slots=True)
class ChosenPlace:
    """The decisions file: in the container, as the user sees it, and its folders.

    `roots` (the folders an audit would analyse, in host paths) start a new file.
    """

    target: Path
    host: str
    roots: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Selection:
    """Files picked on a page, and the search that found them."""

    photos: tuple[PhotoVersion, ...]
    found_by: str = ""


class ChosenStore:
    """Adds files to the `chosen` key of the decisions file, or takes them out."""

    def __init__(self, place: ChosenPlace, mapper: HostPathMapper) -> None:
        """Work on one decisions file.

        Args:
            place: The file.
            mapper: Writes the paths as the user knows them (host paths).
        """
        self.place = place
        self._mapper = mapper

    def on_disk(self) -> tuple[ChosenFile, ...]:
        """Read the files set aside, from the disk.

        Returns:
            Them; none without a decisions file.

        Raises:
            DecisionsError: The file is not a decisions file.
        """
        if not self.place.target.exists():
            return ()
        return read_decisions(self.place.target).chosen

    def paths(self) -> frozenset[str]:
        """The host paths of the files set aside, to mark or count them on a page.

        Returns:
            Them; none when the file cannot be read.
        """
        try:
            return frozenset(file.path for file in self.on_disk())
        except MediaHygieneError:
            return frozenset()

    def add(self, selection: Selection) -> tuple[ChosenFile, ...]:
        """Set files aside: saved, then read back.

        A file chosen again keeps its new version and search.

        Args:
            selection: The files and the search that found them.

        Returns:
            Every file set aside, as read back from the disk.

        Raises:
            DecisionsError: The file is not a decisions file.
            OSError: It cannot be written.
        """
        unique = {
            file.path: file
            for file in (
                ChosenFile(
                    path=self._mapper.to_host(photo.path),
                    size=photo.size,
                    mtime_ns=photo.mtime_ns,
                    found_by=selection.found_by,
                )
                for photo in selection.photos
            )
        }
        return self._save(list(unique.values()), frozenset(unique))

    def remove(self, photos: Iterable[PhotoVersion]) -> tuple[ChosenFile, ...]:
        """Take files out of the set aside: saved, then read back.

        Args:
            photos: The files.

        Returns:
            Every file still set aside, as read back from the disk.

        Raises:
            DecisionsError: The file is not a decisions file.
            OSError: It cannot be written.
        """
        paths = frozenset(self._mapper.to_host(photo.path) for photo in photos)
        return self._save([], paths)

    def _save(
        self, added: list[ChosenFile], replaced: frozenset[str]
    ) -> tuple[ChosenFile, ...]:
        """Write the decisions file with its `chosen` key changed, then read it back.

        Args:
            added: The files to add.
            replaced: The paths whose previous entry goes.

        Returns:
            The files set aside, read back from the disk.
        """
        target = self.place.target
        base = (
            read_decisions(target)
            if target.exists()
            else DecisionsFile(version=1, roots=self.place.roots)
        )
        kept = [file for file in base.chosen if file.path not in replaced]
        chosen = tuple(sorted((*kept, *added), key=lambda file: file.path))
        write_decisions(target, base.model_copy(update={"chosen": chosen}))
        return self.on_disk()


def chosen_size(files: Iterable[ChosenFile]) -> int:
    """The bytes of the files set aside.

    Args:
        files: The files.

    Returns:
        Their total size.
    """
    return sum(file.size for file in files)
