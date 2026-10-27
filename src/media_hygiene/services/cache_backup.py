r"""`media-hygiene backup` (0352): the index and the settings in one archive.

`/cache` is a named Docker volume: a `docker volume prune`, a reset of Docker Desktop
or a new WSL erases it, and with it the index (digests, visual facts, tags,
descriptions, meanings, faces: hours to compute again). The archive goes to
`/backups`, which `mh` mounts from `$HOME\media-hygiene\backups` for `backup` and
`restore` only. It is proven by reading it back from the disk (`backup_archive`), and
the `KEPT` most recent archives are kept, older ones removed.
"""

from __future__ import annotations

import json
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.backup_archive import (
    CONFIG_PREFIX,
    FORMAT,
    INDEX_MEMBER,
    MANIFEST,
    BackupError,
    Manifest,
    copy_index,
    digest,
    index_facts,
)
from media_hygiene.services.backup_check import checked
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

PREFIX: Final = "mh-backup-"
SUFFIX: Final = ".zip"
# The archives kept in `/backups`; the older ones are removed after a new one.
KEPT: Final = 3
_STAMP: Final = "%Y%m%d-%H%M%S"
_DRAFT: Final = ".part"
_PACKAGE: Final = "media-hygiene"


@dataclass(frozen=True, slots=True)
class Backup:
    """An archive written and read back."""

    path: Path
    size: int  # bytes, read from the disk
    manifest: Manifest  # as read back from the archive
    removed: tuple[Path, ...] = ()  # the older archives rotated out


def backups_folder(runtime: Runtime) -> Path:
    """The folder of the archives, checked mounted and writable.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        It, in the container.

    Raises:
        MountError: It is not mounted, or not writable.
    """
    if not runtime.persistent(MountKind.BACKUPS):
        raise MountError(
            _("The backups are written to /backups, which is not mounted."),
            _(
                "mh mounts it for backup and restore; with docker run, add "
                '-v "$HOME\\media-hygiene\\backups:/backups".'
            ),
        )
    ensure_writable(runtime, MountKind.BACKUPS)
    return runtime.locations.backups_dir


def archives(folder: Path) -> list[Path]:
    """The archives of a folder, oldest first (by time written, then by name).

    Args:
        folder: The folder.

    Returns:
        Them.
    """
    return sorted(
        folder.glob(f"{PREFIX}*{SUFFIX}"),
        key=lambda path: (path.stat().st_mtime_ns, path.name),
    )


def make_backup(runtime: Runtime, spared: Path | None = None) -> Backup:
    """Write an archive of the index and of `/config`, prove it, rotate the old ones.

    Args:
        runtime: Settings, mount points and output.
        spared: An archive never rotated out (the one a restore is putting back).

    Returns:
        The archive, as read back.

    Raises:
        MountError: No index to keep, or `/backups` cannot be written.
        BackupError: The archive written does not read back whole (removed).
    """
    folder = backups_folder(runtime)
    index = runtime.locations.index_file
    if not runtime.persistent(MountKind.CACHE) or not index.is_file():
        raise MountError(_("There is no index to back up yet: run an audit first."))
    name = f"{PREFIX}{datetime.now(UTC).astimezone().strftime(_STAMP)}{SUFFIX}"
    target = _unique(folder / name)
    draft = target.with_name(f".{target.name}{_DRAFT}")
    with tempfile.TemporaryDirectory(dir=folder, prefix=".") as scratch:
        copy = Path(scratch) / INDEX_MEMBER
        copy_index(index, copy)
        _write(runtime, copy, draft)
    try:
        with tempfile.TemporaryDirectory(dir=folder, prefix=".") as scratch:
            manifest = checked(draft, Path(scratch))
    except BackupError:
        draft.unlink(missing_ok=True)
        raise
    draft.replace(target)
    removed = tuple(old for old in archives(folder)[:-KEPT] if old != spared)
    for old in removed:
        old.unlink()
    return Backup(target, target.stat().st_size, manifest, removed)


def _unique(path: Path) -> Path:
    """A name no archive has yet: two backups in the same second get `-2`.

    Args:
        path: The name wished.

    Returns:
        It, or the first free one.
    """
    candidate, number = path, 1
    while candidate.exists():
        number += 1
        candidate = path.with_name(f"{path.stem}-{number}{path.suffix}")
    return candidate


def _write(runtime: Runtime, index: Path, draft: Path) -> None:
    """Write the zip: the index copy, the files of `/config`, the manifest.

    Args:
        runtime: Settings, mount points and output.
        index: The consistent copy of the index.
        draft: The zip written.
    """
    schema, counts = index_facts(index)
    members = {INDEX_MEMBER: digest(index)}
    config = runtime.locations.config_dir
    files = (
        sorted(p for p in config.rglob("*") if p.is_file()) if config.is_dir() else []
    )
    with zipfile.ZipFile(draft, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(index, INDEX_MEMBER)
        for file in files:
            member = CONFIG_PREFIX + file.relative_to(config).as_posix()
            archive.write(file, member)
            members[member] = digest(file)
        manifest = Manifest(version(_PACKAGE), schema, members, counts)
        raw = {"format": FORMAT, **asdict(manifest)}
        archive.writestr(MANIFEST, json.dumps(raw, indent=2, sort_keys=True))
