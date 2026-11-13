"""Pictures named after the version of their file on every tile page (0701).

The library names its tiles `/thumb/<key>.<tag>.jpg` (`search/stable_pictures`, 0673).
The other pages name a picture by a number or a key of their run; they add the
file's version as `?v=<tag>`: `<tag>` the hash `preview_key()` makes of the path,
size, modification time and the way previews are made. A file edited, replaced,
renamed or moved gets another address, so the browser may keep the picture for good
(`immutable`), across runs.

`jpeg_response` checks the tag asked (`asked_from`, set for each request by
`serving`) against the file on the disk: the same, kept for good; another or none,
the rule of the run (`no-cache`, asked again), never kept under a name it no longer
matches. Faces cut out keep the rule of the run: their box may change under the same
photo.
"""

from __future__ import annotations

import json
import sqlite3
from contextvars import ContextVar
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.report.preview_cache import PreviewJob, preview_key

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.scan.models import MediaFile

_PARAM: Final = "v="
_JPEG: Final = ".jpg"
_VERSIONS: Final = (
    "SELECT rowid, path, size, mtime_ns FROM files "
    "WHERE rowid IN (SELECT value FROM json_each(?))"
)
# The tag the request names; one per connection, each served in its own task.
_ASKED: ContextVar[str] = ContextVar("asked_version", default="")


def version_tag(path: Path, size: int, mtime_ns: int) -> str:
    """The tag of one version of a file.

    Args:
        path: The file, in the container.
        size: Its size, in bytes.
        mtime_ns: Its modification time.

    Returns:
        32 hexadecimal characters.
    """
    return preview_key(PreviewJob(path, 0, None), size, mtime_ns).removesuffix(_JPEG)


def disk_tag(path: Path) -> str:
    """The tag of the file as it is on the disk now.

    Args:
        path: The file, in the container.

    Returns:
        Its tag; empty for a file that cannot be read.
    """
    try:
        now = path.stat()
    except OSError:
        return ""
    return version_tag(path, now.st_size, now.st_mtime_ns)


def versioned(url: str, file: MediaFile) -> str:
    """A picture's address with the version of the file, as audited.

    Args:
        url: E.g. `preview/<key>.jpg`.
        file: The file it shows.

    Returns:
        E.g. `preview/<key>.jpg?v=0f3a…`.
    """
    return f"{url}?{_PARAM}{version_tag(file.path, file.size, file.mtime_ns)}"


def versioned_on_disk(url: str, path: Path) -> str:
    """A picture's address with the version of the file on the disk now.

    Args:
        url: E.g. `/thumb/3.jpg`.
        path: The file it shows.

    Returns:
        The address and its tag; as it is for a file that cannot be read.
    """
    tag = disk_tag(path)
    return f"{url}?{_PARAM}{tag}" if tag else url


def tagged(url: str, tag: str) -> str:
    """A picture's address with a tag already known (`index_tags`).

    Args:
        url: E.g. `/thumb/12.jpg`.
        tag: The file's tag; empty when unknown.

    Returns:
        The address and its tag; as it is without one.
    """
    return f"{url}?{_PARAM}{tag}" if tag else url


def index_tags(connection: sqlite3.Connection, keys: Iterable[int]) -> dict[int, str]:
    """The tags of files as the index knows them (0723): one query, never a stat.

    The index row follows the tool's own moves (`sort`, `undo` update the path) and
    the next audit sees the user's: the tag changes with the path, size and time.

    Args:
        connection: The open index.
        keys: The files' keys (`rowid`).

    Returns:
        Each known key's tag; none when the index cannot be read.
    """
    try:
        rows = connection.execute(_VERSIONS, (json.dumps(list(keys)),)).fetchall()
    except sqlite3.Error:
        return {}
    return {
        int(key): version_tag(Path(path), int(size), int(mtime))
        for key, path, size, mtime in rows
    }


def asked_from(query: str) -> None:
    """Remember the tag a request names, for `kept_for_good`.

    Args:
        query: What follows its `?`.
    """
    parts = query.split("&")
    tag = next((p.removeprefix(_PARAM) for p in parts if p.startswith(_PARAM)), "")
    _ASKED.set(tag if tag.isalnum() else "")


def kept_for_good(source: Path) -> bool:
    """Tell whether the request named the version the file has on the disk.

    Args:
        source: The file shown.

    Returns:
        True when the browser may keep the picture for good.
    """
    asked = _ASKED.get()
    return bool(asked) and asked == disk_tag(source)
