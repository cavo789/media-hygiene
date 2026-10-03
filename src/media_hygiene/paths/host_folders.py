r"""Where a container path really lives: the host folder behind its mount.

Two container paths can be one host folder, or one inside the other: `/quarantine`
mounted from `C:\Photos\quarantine` lies inside `/data/c/Photos`. The mount table tells
it: the Windows folder of a Docker Desktop mount, or else the device and the folder of
that device a bind mount shows (`8:1` and `/home/me/Photos`).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Iterable

_WINDOWS: Final = "windows"


@dataclass(frozen=True, slots=True)
class HostFolder:
    r"""A folder of the host: a volume (Windows, or a device) and its path parts."""

    volume: str
    parts: tuple[str, ...]

    @property
    def key(self) -> tuple[str, ...]:
        """The parts as the host compares them (Windows ignores case).

        Returns:
            The parts, case-folded on Windows.
        """
        if self.volume == _WINDOWS:
            return tuple(part.casefold() for part in self.parts)
        return self.parts

    def below(self, relative: Iterable[str]) -> HostFolder:
        """The host folder of a path below this one.

        Args:
            relative: The parts below.

        Returns:
            The deeper folder.
        """
        return HostFolder(self.volume, (*self.parts, *relative))

    def contains(self, other: HostFolder) -> bool:
        """Tell whether `other` is this folder or lies inside it.

        Args:
            other: Another host folder.

        Returns:
            True when both are on one volume and `other` starts with this folder.
        """
        mine, theirs = self.key, other.key
        return self.volume == other.volume and theirs[: len(mine)] == mine

    def relative_to(self, outer: HostFolder) -> tuple[str, ...]:
        """The parts of this folder below `outer`, which must contain it.

        Args:
            outer: A folder containing this one.

        Returns:
            The remaining parts.
        """
        return self.parts[len(outer.parts) :]


def host_folder(device: str, root: str, windows: str | None) -> HostFolder:
    r"""Describe the host folder a mount shows.

    Args:
        device: The `major:minor` of the mounted filesystem.
        root: The folder of that filesystem the mount shows.
        windows: The Windows folder, when Docker Desktop tells it.

    Returns:
        The Windows folder when known; else the device and its folder.
    """
    if windows is not None:
        return HostFolder(_WINDOWS, PureWindowsPath(windows).parts)
    return HostFolder(f"dev:{device}", PurePosixPath(root).parts)


def locate(folders: Iterable[tuple[Path, HostFolder]], path: Path) -> HostFolder | None:
    """Find the host folder of a container path, through the deepest mount holding it.

    Args:
        folders: Every mount point and the host folder it shows.
        path: A container path.

    Returns:
        Its host folder, or None when no mount is known to hold it.
    """
    holding = [(point, host) for point, host in folders if path.is_relative_to(point)]
    if not holding:
        return None
    point, host = max(holding, key=lambda item: len(item[0].parts))
    return host.below(path.relative_to(point).parts)
