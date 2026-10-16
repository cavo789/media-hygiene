r"""The quarantines of this run: `/quarantine`, and one per drive on `/quarantine/<x>`.

`/quarantine` is the default one (with `mh`, the quarantine of `C:`). A drive with a
quarantine of its own has it mounted on `/quarantine/<letter>` (`E:\media-hygiene\
quarantine` on `/quarantine/e`): a file set aside then stays on its drive. Only a
mount counts, so a per-drive quarantine is always persistent; the empty `e` folder
Docker leaves inside the default one for the nested mount is never one, and never a
run either (a run identifier starts with eight digits).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Iterable

_LETTERS: Final = frozenset("abcdefghijklmnopqrstuvwxyz")
_DRIVE_AND_RUN: Final = 2  # `/quarantine/e/<run>/…`: the drive's folder, then a run's


def is_drive_folder(name: str) -> bool:
    """Tell whether a folder of the default quarantine is named like a drive's.

    Args:
        name: A folder name.

    Returns:
        True for one lowercase letter, e.g. `e`.
    """
    return name in _LETTERS


def drive_name(letter: str) -> str:
    """Name a drive as Windows shows it.

    Args:
        letter: Its letter, any case.

    Returns:
        E.g. `E:`.
    """
    return f"{letter.upper()}:"


@dataclass(frozen=True, slots=True)
class Quarantines:
    """The default quarantine and the per-drive ones mounted for this run."""

    default: Path
    by_drive: tuple[tuple[str, Path], ...] = ()  # (`E:`, `/quarantine/e`), sorted

    @classmethod
    def mounted(cls, default: Path, mount_points: Iterable[Path]) -> Quarantines:
        """Find the per-drive quarantines among the mount points.

        Args:
            default: The quarantine mount point (`/quarantine`).
            mount_points: Every mount point of this run.

        Returns:
            The quarantines: `/quarantine/<letter>` mounts are the drives' own.
        """
        drives = sorted(
            (drive_name(point.name), point)
            for point in mount_points
            if point.parent == default and is_drive_folder(point.name)
        )
        return cls(default, tuple(drives))

    @property
    def folders(self) -> tuple[Path, ...]:
        """Every quarantine: the default one first.

        Returns:
            The folders whose runs `status`, `purge` and the menu read.
        """
        return (self.default, *(folder for _drive, folder in self.by_drive))

    @property
    def drive_folders(self) -> tuple[Path, ...]:
        """The per-drive quarantines only.

        Returns:
            Their mount points.
        """
        return tuple(folder for _drive, folder in self.by_drive)

    def unplugged(self, quarantined: str) -> str | None:
        """Tell which drive's quarantine held a file, when it is not mounted now.

        Args:
            quarantined: Where the journal says a file was set aside.

        Returns:
            The drive to plug in, e.g. `E:`; None when its quarantine is mounted or
            it went to the default one.
        """
        path = Path(quarantined)
        if not path.is_relative_to(self.default):
            return None
        parts = path.relative_to(self.default).parts
        if len(parts) <= _DRIVE_AND_RUN or not is_drive_folder(parts[0]):
            return None
        drive = drive_name(parts[0])
        return None if drive in dict(self.by_drive) else drive
