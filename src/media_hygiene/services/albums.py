"""The albums of a run: `albums.json` in the reports folder, followed through the index.

Shared by the pages that add to an album (`search`, `browse`, the burst review) and by
`slideshow --album`. The reports folder is checked writable before each save.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.place import decisions_place
from media_hygiene.services.writable import ensure_writable
from media_hygiene.share.album_api import AlbumDesk
from media_hygiene.share.album_follow import Lookup
from media_hygiene.share.album_store import AlbumsPlace, AlbumStore
from media_hygiene.share.albums import ALBUMS_FILE

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime
    from media_hygiene.share.album_api import AlbumAsked


def album_store(runtime: Runtime) -> AlbumStore:
    """The albums file of the reports folder.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        Its store, following moved files through the index.
    """
    reports = runtime.locations.reports_dir
    target = reports / ALBUMS_FILE
    host = decisions_place(runtime.mapper, reports, target).host
    lookup = Lookup(runtime.locations.index_file, runtime.mapper)
    return AlbumStore(AlbumsPlace(target, host), lookup)


def album_desk(
    runtime: Runtime, pick: Callable[[AlbumAsked], tuple[Path, ...]]
) -> AlbumDesk:
    """The desk answering a page about the albums.

    Args:
        runtime: Settings, mount points and output.
        pick: The files a page's request names.

    Returns:
        It.
    """
    return AlbumDesk(album_store(runtime), pick, partial(_reports_ready, runtime))


def _reports_ready(runtime: Runtime) -> None:
    """Check, before each save, that the reports folder keeps the albums file.

    Args:
        runtime: Settings, mount points and output.

    Raises:
        MountError: It is not mounted, or not writable.
    """
    if not runtime.persistent(MountKind.REPORTS):
        raise MountError(
            _("The albums are saved in /reports: mount it, or they are lost.")
        )
    ensure_writable(runtime, MountKind.REPORTS)
