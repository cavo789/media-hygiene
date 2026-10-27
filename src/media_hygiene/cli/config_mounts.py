"""The mount points table of `media-hygiene config`, and the host folder of a path."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from rich.table import Table

from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import is_read_only

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


# Mounted by `mh` for one command only (`share`, `backup`/`restore`, `--lan`).
_VERB_MOUNTS: Final = frozenset({MountKind.SHARES, MountKind.BACKUPS, MountKind.LAN})


def mounts_table(runtime: Runtime) -> Table:
    """Each mount point, the folder of the user's computer behind it, and its state.

    The data mount point lists every folder mounted below it.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The table.
    """
    table = Table(title=_("Mount points"), title_justify="left")
    for header in (_("Mount"), _("Folder on your computer"), _("State")):
        table.add_column(header, overflow="fold")
    data_dir = runtime.locations.data_dir
    for kind in MountKind:
        if kind in _VERB_MOUNTS and not runtime.persistent(kind):
            continue  # mounted by `mh` for one command only: not a missing mount
        path = runtime.locations.path_of(kind)
        paths = [path]
        if kind is MountKind.DATA:
            paths = list(runtime.mounts.data_roots(data_dir))
        for mount in paths:
            table.add_row(
                str(mount),
                on_host(runtime, mount) or "—",
                _state(runtime, kind, mount),
            )
    return table


def _state(runtime: Runtime, kind: MountKind, path: Path) -> str:
    """Describe whether a mount point is mounted, and how.

    Args:
        runtime: Settings, mount points and output.
        kind: Which mount point.
        path: The mount point, or a folder mounted below `/data`.

    Returns:
        The translated, coloured state.
    """
    mounted = (
        path in runtime.mounts.mount_points
        if kind is MountKind.DATA
        else runtime.persistent(kind)
    )
    if not mounted and kind is MountKind.DATA:
        return _("[yellow]not mounted[/] — nothing to analyse")
    if not mounted:
        return _("[yellow]not mounted[/] — nothing kept after the run")
    if path.is_dir() and is_read_only(path):
        return _("[cyan]read-only[/]")
    return _("[green]mounted[/]")


def on_host(runtime: Runtime, path: Path) -> str | None:
    r"""Return the folder of the user's computer behind a container path, when known.

    Args:
        runtime: Settings, mount points and output.
        path: A container path.

    Returns:
        E.g. `C:\Users\me\media-hygiene\config`, or None (Docker volume, unknown).
    """
    host = runtime.mapper.to_host(path)
    return None if host == str(path) else host
