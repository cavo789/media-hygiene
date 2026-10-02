"""What `classify` needs of each file, read from the walk and the index."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.models import MediaInput
from media_hygiene.paths.host_paths import is_within

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.classify.engine import Scope
    from media_hygiene.index.repository import FactsRepository
    from media_hygiene.scan.models import MediaFile
    from media_hygiene.services.runtime import Runtime


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
        Its input.
    """
    facts = index.get(file)
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
