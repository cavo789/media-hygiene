"""The tiles of `import --pick` (0590), what is left out, the copy's progress."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.console.formatting import human_size
from media_hygiene.constants import VIDEO_EXTENSIONS
from media_hygiene.review.near_views import folder_and_name
from media_hygiene.review.views import ORIGINAL_LINK, PREVIEW_LINK

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.copy_in import CopyJob
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.scan.progress import Step

LEFT_OUT_FILE: Final = "import-left-out.json"
_FROZEN: Final = ConfigDict(frozen=True, extra="forbid")
_KEY_LENGTH: Final = 16


class ImportTile(BaseModel):
    """One file only the folder holds, as the page shows it."""

    model_config = _FROZEN

    key: str
    name: str
    folder: str  # where it lies, as Windows names it
    target: str  # where its copy goes, as Windows names it
    size: str
    video: bool
    preview: str
    original: str
    left_out: bool


class ImportDone(BaseModel):
    """What the copy did, the copies read back from the disk."""

    model_config = _FROZEN

    run_id: str
    copied: int
    failed: int


class ImportPickState(BaseModel):
    """`GET /api/state`: the tiles, and where the copy is."""

    model_config = _FROZEN

    tiles: tuple[ImportTile, ...]
    copying: bool = False
    done: int = 0
    total: int = 0
    result: ImportDone | None = None
    failure: str = ""


def tile_key(source: Path) -> str:
    """The key of a file: stable for its path, safe in a URL.

    Args:
        source: The file, in the container.

    Returns:
        The key.
    """
    digest = hashlib.sha256(str(source).encode("utf-8", "surrogateescape"))
    return digest.hexdigest()[:_KEY_LENGTH]


def read_left_out(file: Path) -> frozenset[str]:
    """Read the source paths left out, from the disk.

    Args:
        file: The file of the choices.

    Returns:
        They; none for a file missing or damaged.
    """
    try:
        said = json.loads(file.read_text("utf-8"))
    except OSError, ValueError:
        return frozenset()
    if not isinstance(said, list):
        return frozenset()
    return frozenset(str(path) for path in said)


@dataclass(slots=True)
class Copying:
    """Where the copy is, written by its thread, read by the page."""

    done: int = 0
    total: int = 0

    def start(self, step: Step, total: int | None) -> None:
        """Begin a step.

        Args:
            step: Its title (unused).
            total: The files to copy.
        """
        del step
        self.total = total or 0
        self.done = 0

    def advance(self, weight: int = 1) -> None:
        """One more file.

        Args:
            weight: Unused.
        """
        del weight
        self.done += 1

    def current(self, text: str) -> None:
        """Ignored: the tiles say which files.

        Args:
            text: What is being done.
        """

    def stop(self) -> None:
        """Ignored: the state says the copy has ended."""


def import_tile(
    job: CopyJob, mapper: HostPathMapper, left_out: frozenset[str]
) -> ImportTile:
    """Describe one file.

    Args:
        job: The copy.
        mapper: Names a container path as Windows does.
        left_out: The source paths left out.

    Returns:
        Its tile.
    """
    folder, name = folder_and_name(mapper.to_host(job.source))
    key = tile_key(job.source)
    suffix = job.source.suffix.lower()
    return ImportTile(
        key=key,
        name=name,
        folder=folder,
        target=mapper.to_host(job.target),
        size=_size(job.source),
        video=suffix in VIDEO_EXTENSIONS,
        preview=f"{PREVIEW_LINK}{key}.jpg",
        original=f"{ORIGINAL_LINK}{key}{suffix}",
        left_out=str(job.source) in left_out,
    )


def _size(path: Path) -> str:
    """The size of a file, said.

    Args:
        path: The file.

    Returns:
        Its size; empty when it went away (a disk unplugged).
    """
    try:
        return human_size(path.stat().st_size)
    except OSError:
        return ""
