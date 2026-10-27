"""An archive of `backup` read back (0352): every member against its SHA-256.

The index is extracted to a temporary folder and checked whole (`PRAGMA
integrity_check`), its rows counted against the manifest: a damaged archive is
refused before anything is overwritten. A member name leaving that folder (`..`) is
refused unread.
"""

from __future__ import annotations

import json
import zipfile
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.services.backup_archive import (
    CONFIG_PREFIX,
    INDEX_MEMBER,
    MANIFEST,
    BackupError,
    Manifest,
    digest,
    index_facts,
)

if TYPE_CHECKING:
    from pathlib import Path

_CHUNK: Final = 1 << 20


def _not_backup() -> BackupError:
    """The refusal of a file that is not an archive of `backup`.

    Returns:
        It.
    """
    return BackupError(
        _("This file is not an mh backup: its manifest is missing or unreadable.")
    )


def read_manifest(archive: zipfile.ZipFile) -> Manifest:
    """Read the manifest of an open archive.

    Args:
        archive: The archive.

    Returns:
        Its manifest.

    Raises:
        BackupError: No manifest, or one that cannot be read.
    """
    try:
        raw = json.loads(archive.read(MANIFEST))
        return Manifest(
            str(raw["version"]),
            int(raw["schema"]),
            {str(k): str(v) for k, v in raw["members"].items()},
            {str(k): int(v) for k, v in raw["counts"].items()},
        )
    except (KeyError, ValueError, TypeError, AttributeError) as error:
        raise _not_backup() from error


def _safe(name: str) -> bool:
    """Tell whether a member name stays inside the folder it is extracted to.

    Args:
        name: A member of the manifest.

    Returns:
        True for the index, or a file below `config/` without `..`.
    """
    parts = name.split("/")
    return name == INDEX_MEMBER or (
        name.startswith(CONFIG_PREFIX) and ".." not in parts and "" not in parts[1:]
    )


def checked(path: Path, scratch: Path) -> Manifest:
    """Open an archive, check every member's SHA-256 and the index it holds.

    Args:
        path: The archive.
        scratch: An empty folder where the index is extracted, to `INDEX_MEMBER`.

    Returns:
        Its manifest, the counts read back from the extracted index.

    Raises:
        BackupError: Not a zip, a member altered or missing, a damaged index.
    """
    try:
        with zipfile.ZipFile(path) as archive:
            manifest = read_manifest(archive)
            altered = _extracted(archive, manifest, scratch)
    except (zipfile.BadZipFile, KeyError, OSError) as error:
        raise BackupError(
            _("The backup {name} cannot be read: {why}.").format(
                name=path.name, why=error
            )
        ) from error
    if altered is not None:
        raise BackupError(
            _(
                "The backup {name} is damaged: {member} differs from its manifest."
            ).format(name=path.name, member=altered)
        )
    schema, counts = index_facts(scratch / INDEX_MEMBER)
    if schema != manifest.schema or counts != manifest.counts:
        raise BackupError(
            _(
                "The backup {name} is damaged: its index differs from its manifest."
            ).format(name=path.name)
        )
    return manifest


def _extracted(
    archive: zipfile.ZipFile, manifest: Manifest, scratch: Path
) -> str | None:
    """Extract every member named by the manifest, checking its SHA-256.

    Args:
        archive: The open archive.
        manifest: Its manifest.
        scratch: The folder extracted to.

    Returns:
        The first member that differs from its digest, or None.

    Raises:
        BackupError: The manifest lacks the index, or names a member outside.
    """
    if INDEX_MEMBER not in manifest.members or not all(map(_safe, manifest.members)):
        raise _not_backup()
    for name, expected in manifest.members.items():
        target = scratch / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.open(name) as member, target.open("wb") as copy:
            while chunk := member.read(_CHUNK):
                copy.write(chunk)
        if digest(target) != expected:
            return name
    return None
