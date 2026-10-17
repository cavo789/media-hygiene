"""What `classify` needs of each file, read from the walk and the index."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Protocol

from media_hygiene.classify.models import MediaInput
from media_hygiene.index.former_names import former_of
from media_hygiene.index.takeout_rows import takeout_of
from media_hygiene.paths.host_paths import is_within
from media_hygiene.scan.metadata import MediaMetadata

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.classify.engine import Scope
    from media_hygiene.index.facts import FileFacts
    from media_hygiene.index.repository import FactsRepository
    from media_hygiene.scan.models import MediaFile
    from media_hygiene.scan.takeout_facts import TakeoutFacts
    from media_hygiene.services.runtime import Runtime


class ListedFile(Protocol):
    """A file as a walk or the index lists it: where it is, its size and mtime."""

    @property
    def path(self) -> Path:
        """Container path."""

    @property
    def size(self) -> int:
        """Bytes."""

    @property
    def mtime_ns(self) -> int:
        """Last modification, in nanoseconds."""


@dataclass(frozen=True, slots=True)
class ClassifyInputs:
    """The files of a run and what the index knows of them, and their scope."""

    files: tuple[MediaInput, ...]
    scope: Scope


def media_input(file: MediaFile, root: Path, index: FactsRepository) -> MediaInput:
    """What `classify` needs of one file.

    Args:
        file: The file.
        root: The mounted folder it lies in.
        index: The facts of the audit.

    Returns:
        Its input, with what its Takeout `.json` says and where the copies `clean`
        removed lay.
    """
    found = input_of(file, root, index.get(file))
    found = replace(found, former=former_of(index.connection, file.path))
    return with_takeout(found, takeout_of(index.connection, file.path))


def with_takeout(file: MediaInput, takeout: TakeoutFacts | None) -> MediaInput:
    """Add what a Google Photos Takeout `.json` says of a file.

    Its position stands for the file's own when the file holds none: the `place`
    and `trip` rules and the place words count it like a GPS position.

    Args:
        file: The input.
        takeout: The facts of its `.json`, or None.

    Returns:
        The input, completed.
    """
    if takeout is None:
        return file
    metadata = file.metadata
    if takeout.located and not (metadata is not None and metadata.located):
        position = {"latitude": takeout.latitude, "longitude": takeout.longitude}
        metadata = (metadata or MediaMetadata()).model_copy(update=position)
    return replace(file, takeout=takeout, metadata=metadata)


def input_of(file: ListedFile, root: Path, facts: FileFacts) -> MediaInput:
    """What `classify` and `tags` need of one file, its facts already read.

    Args:
        file: The file: where it is, its size and mtime.
        root: The mounted folder it lies in.
        facts: What the index knows of it.

    Returns:
        Its input.
    """
    return MediaInput(
        path=file.path,
        root=root,
        size=file.size,
        mtime_ns=file.mtime_ns,
        visual=facts.visual,
        metadata=facts.metadata,
        digest=facts.full_digest,
    )


def root_of(path: Path, roots: tuple[Path, ...], runtime: Runtime) -> Path:
    """The mounted folder a file lies in; a whole drive (`/data/c`) when none is.

    Args:
        path: A file.
        roots: Mounted folders.
        runtime: Mount points.

    Returns:
        The root its folders are read from.
    """
    data_dir = runtime.locations.data_dir
    root = next((r for r in roots if is_within(path, r)), data_dir)
    if root == data_dir and path.is_relative_to(data_dir):
        return data_dir / path.relative_to(data_dir).parts[0]
    return root


def duplicates(files: Sequence[MediaInput]) -> int:
    """Count the extra copies the index knows of.

    Args:
        files: The inputs.

    Returns:
        Files that are identical to another one (by SHA-256), minus one per group.
    """
    groups = Counter(file.digest for file in files if file.digest)
    return sum(count - 1 for count in groups.values() if count > 1)


def mounted(target: Path, data_dir: Path) -> bool:
    """Tell whether a target lies in a mounted folder (it may not exist yet).

    Args:
        target: The target root, container path.
        data_dir: The data mount point.

    Returns:
        True when one of its folders below the data mount point exists.
    """
    if not is_within(target, data_dir):
        return False
    return any(
        folder.is_dir()
        for folder in (target, *target.parents)
        if folder != data_dir and is_within(folder, data_dir)
    )
