r"""Where an album goes: `[album] root`, else `Albums` in the `[classify] target`.

The folder must be mounted (links made in the container alone vanish with it), outside
the protected folders, writable, and its name a valid Windows folder name.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import AlbumError, MountError
from media_hygiene.i18n import _
from media_hygiene.paths.host_paths import is_within
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import is_writable
from media_hygiene.services.writable import writable_tip

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

# What Windows refuses in a folder name, control characters included.
_FORBIDDEN: Final = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_DOTS: Final = frozenset({".", ".."})


def album_folder(runtime: Runtime, name: str) -> Path:
    """Find the folder of an album, and check that links may be made in it.

    Args:
        runtime: Settings, mount points and output.
        name: The album's name, as typed.

    Returns:
        The album folder (container path).

    Raises:
        AlbumError: The name is not a folder name, or no folder holds the albums.
        MountError: The folder is not mounted, protected, or not writable.
    """
    clean = name.strip()
    if not clean or clean in _DOTS or _FORBIDDEN.search(clean) or clean[-1] == ".":
        raise AlbumError(
            _("'{name}' cannot be a folder name.").format(name=name),
            _('Give the album a plain name, e.g. "Christmas" or "Best of 2016".'),
        )
    settings = runtime.settings
    if settings.album.root:
        root = runtime.mapper.to_container(settings.album.root)
    elif settings.classify.target:
        root = runtime.mapper.to_container(settings.classify.target) / _("Albums")
    else:
        raise AlbumError(
            _(
                "No folder for the albums: neither album.root nor classify.target "
                "is set."
            ),
            _(
                "Set album.root in config.toml, a folder on the disk of your photos, "
                "e.g. root = 'C:\\Photos\\Albums'."
            ),
        )
    folder = root / clean
    _check(runtime, folder)
    return folder


def _check(runtime: Runtime, folder: Path) -> None:
    """Refuse a folder lost with the container, protected, or not writable.

    Args:
        runtime: Settings, mount points and output.
        folder: The album folder (container path).

    Raises:
        MountError: Links may not be made there.
    """
    host = runtime.mapper.to_host(folder)
    data_dir = runtime.locations.data_dir
    mounted = [r for r in runtime.mounts.data_roots(data_dir) if is_within(folder, r)]
    lost = bool(mounted) and mounted[0] == data_dir
    if not mounted or (lost and not runtime.persistent(MountKind.DATA)):
        raise MountError(
            _(
                "{path} is not in a mounted folder: an album made there would vanish "
                "with the container."
            ).format(path=host),
            _("Mount the folder of your photos that holds it, without ':ro'."),
        )
    protected = runtime.settings.folders.protected
    if any(is_within(folder, runtime.mapper.to_container(p)) for p in protected):
        raise MountError(
            _(
                "{path} is inside a protected folder: nothing is ever added there."
            ).format(path=host),
            _("Set album.root in config.toml to a folder outside it."),
        )
    existing = next(path for path in (folder, *folder.parents) if path.exists())
    if not is_writable(existing):
        raise MountError(
            _("The container cannot write to {folders}.").format(folders=host),
            writable_tip((existing,)),
        )
