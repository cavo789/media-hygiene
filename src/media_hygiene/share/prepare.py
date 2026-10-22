"""The folder and the zip of an album made ready to send (0296).

Everything is written under the shares folder (`/shares`, mounted by `mh` for `share`
only), never next to the photos: a folder named after the album, holding one JPEG per
photo, and `<album>.zip` beside it. The copies go into a draft folder first; once all
are written, an earlier folder of the same album is replaced by it, then the zip is
written (a draft, then renamed). What is said at the end is read back from the disk.
"""

from __future__ import annotations

import re
import shutil
import zipfile
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from pathlib import Path

_UNSAFE: Final = re.compile(r'[\\/:*?"<>|\x00-\x1f]')  # what Windows refuses in a name
_FALLBACK: Final = "album"
_JPEG: Final = ".jpg"
_ZIP: Final = ".zip"
_DRAFT: Final = ".partial"


def folder_name(album: str) -> str:
    """The name of an album's folder: what Windows refuses replaced by `_`.

    Args:
        album: The album's name.

    Returns:
        A name of one folder, never empty, `.` nor `..`.
    """
    name = _UNSAFE.sub("_", " ".join(album.split())).strip(" .")
    return name or _FALLBACK


@dataclass(frozen=True, slots=True)
class Sent:
    """What the disk holds once the album is ready: read back, not remembered."""

    folder: Path
    archive: Path
    photos: int  # files in the folder
    size: int  # their bytes
    zipped: int  # files in the zip
    zip_size: int
    replaced: bool  # an earlier folder of the album was replaced


class Delivery:
    """The copies of one album, written into a draft folder, then put in place."""

    def __init__(self, shares: Path, album: str) -> None:
        """Start an empty draft folder for an album.

        Args:
            shares: The shares folder, in the container.
            album: The album's name.
        """
        self._name = folder_name(album)
        self._shares = shares
        self._draft = shares / f".{self._name}{_DRAFT}"
        shutil.rmtree(self._draft, ignore_errors=True)  # left by a run stopped
        self._draft.mkdir(parents=True)
        self._taken: set[str] = set()

    def add(self, stem: str, data: bytes) -> None:
        """Write one copy: the photo's name, `_1` added to a name taken already.

        Args:
            stem: The photo's name, without its extension.
            data: The JPEG.
        """
        name = f"{stem}{_JPEG}"
        number = 0
        while name.casefold() in self._taken:  # Windows ignores the case
            number += 1
            name = f"{stem}_{number}{_JPEG}"
        self._taken.add(name.casefold())
        (self._draft / name).write_bytes(data)

    def discard(self) -> None:
        """Remove the draft folder, if any: a run stopped replaces nothing earlier."""
        shutil.rmtree(self._draft, ignore_errors=True)

    def finish(self) -> Sent:
        """Put the folder in place, write the zip, then read both back.

        Returns:
            What the disk holds.
        """
        folder = self._shares / self._name
        replaced = folder.exists()
        if replaced:
            shutil.rmtree(folder)
        self._draft.replace(folder)
        archive = self._shares / f"{self._name}{_ZIP}"
        draft = archive.with_name(f".{archive.name}{_DRAFT}")
        files = sorted(path for path in folder.iterdir() if path.is_file())
        # JPEGs do not shrink: stored as they are, the zip is written fast.
        with zipfile.ZipFile(draft, "w", zipfile.ZIP_STORED) as written:
            for path in files:
                written.write(path, f"{self._name}/{path.name}")
        draft.replace(archive)
        return read_back(folder, archive, replaced=replaced)


def read_back(folder: Path, archive: Path, *, replaced: bool) -> Sent:
    """Count what the folder and the zip hold, from the disk.

    Args:
        folder: The album's folder.
        archive: Its zip.
        replaced: An earlier folder was replaced.

    Returns:
        The counts and the sizes.
    """
    files = [path for path in folder.iterdir() if path.is_file()]
    with zipfile.ZipFile(archive) as written:
        zipped = len(written.namelist())
    return Sent(
        folder=folder,
        archive=archive,
        photos=len(files),
        size=sum(path.stat().st_size for path in files),
        zipped=zipped,
        zip_size=archive.stat().st_size,
        replaced=replaced,
    )
