"""Tile pictures named after the version of the file they show (0673).

A tile's picture is `/thumb/<key>.<tag>.jpg`: `<key>` the file's row in the index,
`<tag>` the hash `preview_key()` makes of its path, size, modification time, the
picture's size and the way previews are made. A file edited, replaced, renamed or
moved gets another tag, so the browser may keep a picture for good
(`Cache-Control: private, max-age=…, immutable`) and never ask again, even after the
server restarted. The tag reveals nothing: a hash.

The server checks the tag against the index (another one: 404, the page lists again),
then the file on the disk: a file changed since the index saw it is still shown, but
under today's rule (`no-cache`, asked again), never kept under a name it no longer
matches.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.report.preview_cache import PreviewJob, preview_key
from media_hygiene.report.thumbnails import REVIEW_EDGE
from media_hygiene.search.thumbs import GRID_EDGE

if TYPE_CHECKING:
    from media_hygiene.index.descriptions import PhotoVersion

_SEPARATOR: Final = "."
JPEG: Final = ".jpg"
THUMB_PREFIX: Final = "/thumb/"
PREVIEW_PREFIX: Final = "/preview/"


def picture_tag(photo: PhotoVersion, edge: int) -> str:
    """The tag of one version of a file at one size.

    Args:
        photo: The file and its version, as the index knows it.
        edge: The picture's longer side, in pixels.

    Returns:
        32 hexadecimal characters.
    """
    job = PreviewJob(photo.path, edge, None)
    return preview_key(job, photo.size, photo.mtime_ns).removesuffix(JPEG)


def picture_path(prefix: str, key: int, tag: str) -> str:
    """The path of a tile's picture.

    Args:
        prefix: `/thumb/` or `/preview/`.
        key: The file's key in the index.
        tag: Its `picture_tag`.

    Returns:
        E.g. `/thumb/12.0f3a….jpg`.
    """
    return f"{prefix}{key}{_SEPARATOR}{tag}{JPEG}"


def tile_pictures(key: int, photo: PhotoVersion) -> dict[str, str]:
    """The small and the large picture of a tile, named after the file's version.

    Args:
        key: The file's key in the index.
        photo: The file and its version, as the index knows it.

    Returns:
        `thumb` and `preview` paths.
    """
    return {
        "thumb": picture_path(THUMB_PREFIX, key, picture_tag(photo, GRID_EDGE)),
        "preview": picture_path(PREVIEW_PREFIX, key, picture_tag(photo, REVIEW_EDGE)),
    }


def parsed_name(name: str) -> tuple[int, str] | None:
    """Read the key and the tag of a picture's name (`12` or `12.0f3a…`).

    Args:
        name: The path asked for, without its prefix and `.jpg`.

    Returns:
        The key and the tag (empty for a name without one), None for no key.
    """
    key, _dot, tag = name.partition(_SEPARATOR)
    if not key.isdigit() or (tag and not tag.isalnum()):
        return None
    return int(key), tag


def still_this_version(photo: PhotoVersion) -> bool:
    """Tell whether the file on the disk is still the version the index saw.

    Args:
        photo: The file and its version, as the index knows it.

    Returns:
        False for a file changed (size or time) or gone since.
    """
    try:
        now = photo.path.stat()
    except OSError:
        return False
    return (now.st_size, now.st_mtime_ns) == (photo.size, photo.mtime_ns)
