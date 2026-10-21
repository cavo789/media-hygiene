r"""The target of `mh backup` and the photo folders copied into it (0264).

The target is a folder of its own (`\\NAS\backup_photos`), mounted read-only: only
Windows writes there. It is refused when it is, holds or lies in a photo folder or a
backup folder (compared, never changed). Each photo folder goes below it by its own
path, the drive as a folder: `C:\Photos` into `<target>\C\Photos`, so two folders of
the same name never meet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.paths.host_paths import is_within
from media_hygiene.paths.unc import UNC_FOLDER
from media_hygiene.services.backup_place import Target, host_parts

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class Source:
    """A photo folder copied into the target."""

    point: Path  # `/data/c/Photos`
    host: str  # `C:\Photos`
    prefix: str  # `C/Photos`, its folder in the target


def backup_target(runtime: Runtime, host: str) -> Target:
    r"""Find the target in the container; refuse one that overlaps a folder of the tool.

    Args:
        runtime: Settings, mount points and output.
        host: The target as typed (`\\NAS\backup_photos`, `E:\Backup`).

    Returns:
        The target.

    Raises:
        MountError: It is not mounted, or it overlaps a photo or backup folder.
    """
    target = Target(runtime.mapper.to_container(host), host.rstrip("/\\") or host)
    for folder, point in _others(runtime, target):
        if is_within(point, target.point) or is_within(target.point, point):
            raise MountError(
                _(
                    "The backup target {target} overlaps {folder}: choose a folder "
                    "of its own, outside your photo folders and backups."
                ).format(target=target.host, folder=folder)
            )
    if not target.point.is_dir():
        raise MountError(
            _("The backup target {target} is not mounted: nothing was read.").format(
                target=target.host
            ),
            _("Type mh backup in Windows PowerShell: it mounts it."),
        )
    return target


def backup_sources(runtime: Runtime, target: Target) -> tuple[Source, ...]:
    """List the photo folders mounted, each with its folder in the target.

    Args:
        runtime: Settings, mount points and output.
        target: The target, left out of the folders.

    Returns:
        The photo folders, in path order; the backups and the target left out.
    """
    backups = _backups(runtime)
    sources: list[Source] = []
    for point in _photos(runtime):
        if is_within(point, target.point):
            continue
        if any(is_within(point, backup) for backup in backups):
            continue
        host = runtime.mapper.to_host(point)
        sources.append(Source(point, host, "/".join(host_parts(host))))
    return tuple(sources)


def _others(runtime: Runtime, target: Target) -> list[tuple[str, Path]]:
    """The photo folders and backups the target must not overlap.

    Args:
        runtime: Settings, mount points and output.
        target: The target, whose own mount is not a photo folder.

    Returns:
        Each one's host path and container path.
    """
    photos = [point for point in _photos(runtime) if point != target.point]
    folders = [*photos, *_backups(runtime)]
    return [(runtime.mapper.to_host(point), point) for point in folders]


def _photos(runtime: Runtime) -> list[Path]:
    """The folders mounted below `/data` that may be photo folders.

    A share of a NAS (`/data/unc/…`) is never one: `mh` mounts a NAS as a backup, or
    as the target, whose share may hold it.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        Their container paths, in path order.
    """
    data_dir = runtime.locations.data_dir
    shares = data_dir / UNC_FOLDER
    return [
        point
        for point in runtime.mounts.data_roots(data_dir)
        if point != data_dir and not is_within(point, shares)
    ]


def _backups(runtime: Runtime) -> list[Path]:
    """The backup folders, compared and never changed (0205), in the container.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        Their container paths.
    """
    mapper = runtime.mapper
    return [mapper.to_container(folder) for folder in runtime.settings.folders.backups]
