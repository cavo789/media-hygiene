r"""Which host drive a container path lies on, and which quarantine receives a file.

Only the mount table tells the drive: the Windows source Docker Desktop leaves for each
bind mount (`E:\Photos` on `/data/e/Photos`). A named volume, or a Linux host, has no
drive: the answer is then None and nothing is said about drives.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

_DRIVE_LENGTH = 2  # "E:"


@dataclass(frozen=True, slots=True)
class Drives:
    """The drive letters behind the mount points, from their Windows sources."""

    sources: tuple[tuple[Path, str], ...] = ()

    def drive_of(self, path: Path) -> str | None:
        r"""Return the drive of the deepest mount holding `path`.

        Args:
            path: A container path.

        Returns:
            The drive, e.g. `E:`, or None when no mount with a Windows source holds it.
        """
        holding = [
            (point, source)
            for point, source in self.sources
            if path.is_relative_to(point)
        ]
        if not holding:
            return None
        _point, source = max(holding, key=lambda item: len(item[0].parts))
        drive = source[:_DRIVE_LENGTH]
        return drive.upper() if drive.endswith(":") else None


@dataclass(frozen=True, slots=True)
class QuarantineRoute:
    """Which quarantine receives a file set aside, and on which drive it lies.

    `default` (`/quarantine`) receives every file whose drive has no quarantine of
    its own in `by_drive` (empty until a quarantine per drive is mounted): callers ask
    this route rather than the mount point.
    """

    drives: Drives
    default: Path
    by_drive: tuple[tuple[str, Path], ...] = ()

    def receiving(self, path: Path) -> Path:
        """Return the quarantine a file goes to.

        Args:
            path: The file set aside.

        Returns:
            The quarantine of its drive, else the default one.
        """
        drive = self.drives.drive_of(path)
        own = (folder for name, folder in self.by_drive if name == drive)
        return next(own, self.default)

    def crosses_drive(self, path: Path) -> tuple[str, str] | None:
        """Tell whether setting a file aside copies it to another drive.

        Args:
            path: The file set aside.

        Returns:
            Its drive and the quarantine's, when both are known and differ; else None.
        """
        source = self.drives.drive_of(path)
        target = self.drives.drive_of(self.receiving(path))
        if source is None or target is None or source == target:
            return None
        return source, target
