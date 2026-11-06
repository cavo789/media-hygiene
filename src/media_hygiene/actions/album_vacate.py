"""Empty an album's old folder of the links the tool made, journaled (0582).

Once an album is made again in the new `[album] root`, its old folder keeps only what
the tool did not make: a name is removed only when a journal proves an album run made
it and it still is a second name of its photo. Each removal is an `unlink` (`undo`
makes it again from the photo); the marker goes last, as a second name of the new
album's marker, then the folder, once empty.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.actions.album_readme import readme_of
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.outcome import Incident, why
from media_hygiene.actions.sort_moves import file_of
from media_hygiene.constants import ALBUM_MARKER, ALBUM_README_NAMES

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.actions.journaled import JournaledChanges
    from media_hygiene.actions.outcome import Tally


@dataclass(frozen=True, slots=True)
class Vacated:
    """What became of an old album folder."""

    removed: int  # links removed
    kept: tuple[Path, ...]  # files the journals do not prove the tool made
    folder_removed: bool


def _second_name(link: Path, photo: Path) -> bool:
    """Whether a name still is another name of a photo.

    Args:
        link: The name in the old folder.
        photo: The photo it was made from.

    Returns:
        True when both exist and are the same file.
    """
    return link.is_file() and photo.is_file() and link.samefile(photo)


@dataclass(frozen=True, slots=True)
class AlbumVacate:
    """Removes the proven links of an old album folder, then its marker and itself."""

    changes: JournaledChanges
    tally: Tally

    def run(self, old: Path, made: Mapping[Path, Path], marker: Path) -> Vacated:
        """Empty the old folder of what the tool made.

        Args:
            old: The old album folder.
            made: Each link the journals prove made in it, and its photo.
            marker: The new album's marker (the old one's other name for `undo`).

        Returns:
            What was removed and kept.
        """
        removed = 0
        kept: list[Path] = []
        for name in sorted(old.iterdir()):
            if name.name == ALBUM_MARKER:
                continue
            photo = made.get(name)
            if photo is None or not _second_name(name, photo):
                kept.append(name)
            elif self._unlink(name, photo):
                removed += 1
            else:
                kept.append(name)
        if kept or not self.unlink_copy(old / ALBUM_MARKER, marker):
            return Vacated(removed, tuple(kept), folder_removed=False)
        entry = self.changes.entry(file_of(old, (0, 0)), ActionKind.REMOVE_FOLDER)
        self.changes.record(entry, old.rmdir)
        return Vacated(removed, (), folder_removed=True)

    def leave_root(self, root: Path, new_root: Path) -> tuple[Path, ...]:
        """Once its last album left: the old root loses its read-me, then itself (0626).

        Args:
            root: The old folder of the albums.
            new_root: The new one, holding the read-me `undo` makes the old again from.

        Returns:
            The files found there that are not the tool's: they stay, the folder too.
        """
        entries = sorted(root.iterdir())
        strays = tuple(
            p for p in entries if p.is_file() and p.name not in ALBUM_README_NAMES
        )
        if strays or any(p.is_dir() for p in entries):
            return strays
        carried = readme_of(new_root)
        for name in entries:
            if carried is None or not self.unlink_copy(name, carried):
                return ()
        entry = self.changes.entry(file_of(root, (0, 0)), ActionKind.REMOVE_FOLDER)
        try:
            self.changes.record(entry, root.rmdir)
        except OSError as exc:
            self.tally.failed.append(Incident(root, why(exc)))
        return ()

    def unlink_copy(self, old: Path, new: Path) -> bool:
        """Remove a file of the tool in the old place, `undo` makes it from the new.

        Args:
            old: The old marker or read-me.
            new: The new one.

        Returns:
            True when the old folder holds nothing more.
        """
        if not old.exists():
            return True
        if not new.is_file():
            return False
        info = new.stat()
        entry = self.changes.entry(
            file_of(old, (info.st_size, info.st_mtime_ns)), ActionKind.UNLINK
        ).model_copy(update={"keeper": str(new)})
        try:
            self.changes.record(entry, old.unlink)
        except OSError as exc:
            self.tally.failed.append(Incident(old, why(exc)))
            return False
        return True

    def _unlink(self, link: Path, photo: Path) -> bool:
        """Remove one link, journaled with its photo as `keeper`.

        Args:
            link: The link.
            photo: Its other name.

        Returns:
            True when removed.
        """
        entry = self.changes.entry(file_of(link), ActionKind.UNLINK).model_copy(
            update={"keeper": str(photo)}
        )
        try:
            self.changes.record(entry, link.unlink)
        except OSError as exc:
            self.tally.failed.append(Incident(link, why(exc)))
            return False
        return True
