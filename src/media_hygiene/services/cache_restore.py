"""`media-hygiene restore` (0352): an archive of `backup` put back, never blindly.

Order: the archive is checked whole first (SHA-256 of every member, integrity of its
index, a schema this image knows); then the current state is backed up (the undo:
`restore <that archive>`); only then is the index overwritten, through SQLite's
`backup` into the live file (consistent with its journal files), and read back: its
row counts must be those of the manifest. `/config` is restored only when asked:
files written since the backup and absent from it are left in place.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.index.schema import SCHEMA_VERSION
from media_hygiene.services.backup_archive import (
    CONFIG_PREFIX,
    INDEX_MEMBER,
    BackupError,
    Manifest,
    copy_index,
    index_facts,
)
from media_hygiene.services.backup_check import checked
from media_hygiene.services.cache_backup import (
    Backup,
    archives,
    backups_folder,
    make_backup,
)

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class RestoreRequest:
    """What to restore: an archive (None: the most recent), `/config` too or not."""

    archive: str | None = None
    config: bool = False


@dataclass(frozen=True, slots=True)
class Restored:
    """An archive put back, and the backup of what was there before."""

    archive: Path
    manifest: Manifest
    counts: dict[str, int]  # read back from the restored index
    before: Backup | None  # None: there was no index yet
    config: tuple[str, ...] = ()  # the files of `/config` written


def restore_backup(runtime: Runtime, request: RestoreRequest) -> Restored:
    """Check an archive, back up the current state, then put the archive back.

    Args:
        runtime: Settings, mount points and output.
        request: The archive, and whether `/config` is restored too.

    Returns:
        What was restored, read back.

    Raises:
        BackupError: No archive, a damaged one, or one from a newer image.
    """
    folder = backups_folder(runtime)
    archive = _chosen(folder, request.archive)
    index = runtime.locations.index_file
    with tempfile.TemporaryDirectory(dir=folder, prefix=".") as scratch:
        extracted = Path(scratch)
        manifest = checked(archive, extracted)
        if manifest.schema > SCHEMA_VERSION:
            raise BackupError(
                _(
                    "The backup {name} was made by a newer version of media-hygiene: "
                    "type mh update first."
                ).format(name=archive.name)
            )
        before = make_backup(runtime, archive) if index.is_file() else None
        index.parent.mkdir(parents=True, exist_ok=True)
        copy_index(extracted / INDEX_MEMBER, index)
        written = _config(runtime, extracted, manifest) if request.config else ()
    _schema, counts = index_facts(index)
    if counts != manifest.counts:
        raise BackupError(
            _("The restored index differs from the backup {name}.").format(
                name=archive.name
            )
        )
    return Restored(archive, manifest, counts, before, written)


def _chosen(folder: Path, name: str | None) -> Path:
    """The archive named, in the backups folder, or the most recent one.

    Args:
        folder: The backups folder.
        name: A file name (or a path in the container), or None.

    Returns:
        The archive.

    Raises:
        BackupError: None there, or the one named is missing.
    """
    if name is None:
        found = archives(folder)
        if not found:
            raise BackupError(_("There is no backup to restore yet: type mh backup."))
        return found[-1]
    path = Path(name)
    archive = path if path.is_absolute() else folder / path.name
    if not archive.is_file():
        raise BackupError(_("There is no backup named {name}.").format(name=name))
    return archive


def _config(runtime: Runtime, extracted: Path, manifest: Manifest) -> tuple[str, ...]:
    """Write the files of `/config` held by the archive, each one atomically.

    Args:
        runtime: Settings, mount points and output.
        extracted: The folder where the archive was extracted, checked.
        manifest: Its manifest.

    Returns:
        The files written, relative to `/config`.
    """
    config = runtime.locations.config_dir
    written: list[str] = []
    for member in sorted(manifest.members):
        if not member.startswith(CONFIG_PREFIX):
            continue
        relative = member.removeprefix(CONFIG_PREFIX)
        target = config / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        draft = target.with_name(f".{target.name}.restore")
        draft.write_bytes((extracted / member).read_bytes())
        draft.replace(target)
        written.append(relative)
    return tuple(written)
