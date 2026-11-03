"""The folders `mh` gave this page: photos, backups, quarantine; each found or not."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.home_parts import HomeFolder
from media_hygiene.services.quarantines import mounted_quarantines

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


def home_folders(runtime: Runtime) -> tuple[HomeFolder, ...]:
    """Every folder mounted for the photos, then the quarantine.

    Args:
        runtime: Settings, mount points and the mount table.

    Returns:
        One line per folder, in host paths.
    """
    data_dir = runtime.locations.data_dir
    roots = runtime.mounts.data_roots(data_dir)
    backups = {_key(backup) for backup in runtime.settings.folders.backups}
    unseen = {point for point, _drive in runtime.mounts.unseen_drives}
    folders = []
    for root in (root for root in roots if root != data_dir):
        host = runtime.mapper.to_host(root)
        backup = _key(host) in backups
        note, ok = _note(root, seen=root not in unseen)
        role = _("Backup, never changed") if backup else _("Photos")
        folders.append(HomeFolder(path=host, role=role, note=note, ok=ok))
    if runtime.persistent(MountKind.QUARANTINE):
        folders.extend(_quarantines(runtime))
    return tuple(folders)


def _quarantines(runtime: Runtime) -> tuple[HomeFolder, ...]:
    """The default quarantine, then each drive's own, as `mh folders` lists them (0504).

    Args:
        runtime: Settings, mount points and the mount table.

    Returns:
        One line per quarantine, found or not.
    """
    quarantines = mounted_quarantines(runtime)
    sources = dict(runtime.mounts.host_sources)
    named = (
        (_("Quarantine"), quarantines.default),
        *(
            (_("Quarantine of {drive}").format(drive=drive), folder)
            for drive, folder in quarantines.by_drive
        ),
    )
    return tuple(
        HomeFolder(
            path=sources.get(folder, str(folder)),
            role=role,
            note=_("Found") if folder.is_dir() else _("Not found"),
            ok=folder.is_dir(),
        )
        for role, folder in named
    )


def _note(root: Path, *, seen: bool) -> tuple[str, bool]:
    """What can be said of a folder of photos or of a backup.

    Args:
        root: Its mount point.
        seen: False for a drive Docker Desktop cannot see.

    Returns:
        The note, and whether the folder is fine.
    """
    if not seen or not root.is_dir():
        return _("Not found"), False
    try:
        entries = sum(1 for _entry in root.iterdir())
    except OSError:
        return _("Not readable"), False
    if not entries:
        return _("Empty, or a disk unplugged"), False
    return _("{count} entries at its top").format(count=human_number(entries)), True


def _key(path: str) -> str:
    """A host path compared without its case nor its last separator.

    Args:
        path: A host path.

    Returns:
        Its key.
    """
    return path.rstrip("\\/").casefold()
