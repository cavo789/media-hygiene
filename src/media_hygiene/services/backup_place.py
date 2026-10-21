r"""Where the target of `mh backup` is, for the container and for Windows (0264)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Final

_WINDOWS_SEPARATOR: Final = "\\"
# At the target's root: the files set aside by a run, in `.removed/<run>/…` (0264).
REMOVED_FOLDER: Final = ".removed"


@dataclass(frozen=True, slots=True)
class Target:
    """The folder `mh backup` fills: where the container and Windows see it."""

    point: Path
    host: str

    def host_of(self, relative: str) -> str:
        r"""Where Windows finds a path of the target.

        Args:
            relative: A path relative to the target, `/` between folders.

        Returns:
            `\\NAS\backup_photos\C\Photos\a.jpg` (or `/` on a Linux host).
        """
        return host_join(self.host, relative)

    def relative(self, host: str) -> str | None:
        """The path relative to the target of a host path below it.

        Args:
            host: A host path, as `host_of` writes it.

        Returns:
            It, `/` between folders; None for a path outside the target.
        """
        base = host_parts(self.host)
        parts = host_parts(host)
        if [part.casefold() for part in parts[: len(base)]] != [
            part.casefold() for part in base
        ]:
            return None
        rest = parts[len(base) :]
        return "/".join(rest) if rest else None


def host_join(host: str, relative: str) -> str:
    r"""A path below a host folder, written as the host writes it.

    Args:
        host: `C:\Photos`, `\\NAS\share` or `/home/me/Photos`.
        relative: A path below it, `/` between folders.

    Returns:
        `C:\Photos\2024\a.jpg`, or `/` between folders on a Linux host.
    """
    parts = PurePosixPath(relative).parts
    if windows_host(host):
        return str(PureWindowsPath(host, *parts))
    return str(PurePosixPath(host, *parts))


def host_parts(host: str) -> tuple[str, ...]:
    r"""The folders of a host path, its drive or share first, without separators.

    Args:
        host: `C:\Photos`, `\\NAS\share\x` or `/home/me/Photos`.

    Returns:
        `("C", "Photos")`, `("NAS", "share", "x")`, `("home", "me", "Photos")`.
    """
    if not windows_host(host):
        return PurePosixPath(host).parts[1:] if host.startswith("/") else ()
    path = PureWindowsPath(host)
    drive = path.drive.strip(_WINDOWS_SEPARATOR).rstrip(":")
    head = tuple(part for part in drive.split(_WINDOWS_SEPARATOR) if part)
    return (*head, *path.parts[1:])


def windows_host(host: str) -> bool:
    r"""Tell whether a host path is a Windows one: a drive letter or a share.

    Args:
        host: A host path.

    Returns:
        True for `C:\…` or `\\NAS\…`.
    """
    return bool(PureWindowsPath(host).drive)
