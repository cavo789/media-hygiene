"""The `unwanted` decisions of `review --junk` in the decisions file, read back.

The page never trusts its own memory: after each choice the file is read again from the
disk, and the page shows what it found there.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.report.unwanted_decisions import UnwantedEntry
from media_hygiene.review.session_file import stamped_decisions

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.plan.unwanted import UnwantedPhoto

_FROZEN = ConfigDict(frozen=True, extra="forbid")

type PhotoKey = tuple[str, int, int]


class UnwantedDiskEntry(BaseModel):
    """One decided photo as the decisions file holds it on the disk."""

    model_config = _FROZEN

    photo: int
    aside: bool


class UnwantedProof(BaseModel):
    """The decisions file as just read from the disk: when written, how big, what."""

    model_config = _FROZEN

    size: int
    modified: str  # ISO 8601, UTC: the page shows it in local time
    entries: tuple[UnwantedDiskEntry, ...]


def photo_key(mapper: HostPathMapper, photo: UnwantedPhoto) -> PhotoKey:
    """Name a photo as the decisions file does: host path, size, modification time.

    Args:
        mapper: Container to host path translator.
        photo: The photo, as the audit saw it.

    Returns:
        Its key: another version of the file is another photo.
    """
    file = photo.file
    return mapper.to_host(file.path), file.size, file.mtime_ns


def entry_key(entry: UnwantedEntry) -> PhotoKey:
    """Name a decided photo the way `photo_key` names the photos of the audit.

    Args:
        entry: The decision, as the file holds it.

    Returns:
        Its key.
    """
    return entry.path, entry.size, entry.mtime_ns


def photo_entry(key: PhotoKey, photo: UnwantedPhoto, *, aside: bool) -> UnwantedEntry:
    """Write one decision as the decisions file holds it.

    Args:
        key: The photo's key (`photo_key`).
        photo: The photo and its reason.
        aside: True to set it aside, False to keep it.

    Returns:
        The decision.
    """
    path, size, mtime_ns = key
    return UnwantedEntry(
        path=path, size=size, mtime_ns=mtime_ns, reason=photo.reason, aside=aside
    )


def read_unwanted_back(target: Path, keys: Mapping[PhotoKey, int]) -> UnwantedProof:
    """Read the decisions file from the disk, each decision placed on its photo.

    Args:
        target: The decisions file, in the container.
        keys: Every photo of the review, by its key.

    Returns:
        What the file holds; decisions matching no photo are left out.

    Raises:
        DecisionsError: The file cannot be read, or is not a decisions file.
    """
    decisions, (size, modified) = stamped_decisions(target)
    return UnwantedProof(
        size=size,
        modified=modified,
        entries=tuple(
            UnwantedDiskEntry(photo=keys[key], aside=entry.aside)
            for entry in decisions.unwanted
            if (key := entry_key(entry)) in keys
        ),
    )


def unwanted_proven(
    proof: UnwantedProof, expected: Mapping[int, bool | None]
) -> UnwantedProof:
    """Check that the file read back holds the choices just saved.

    Args:
        proof: The file, read back from the disk.
        expected: The choices, by photo rank (None: undecided, so absent).

    Returns:
        The proof, reduced to those photos.

    Raises:
        DecisionsError: The file does not hold one of the choices.
    """
    found = {entry.photo: entry.aside for entry in proof.entries}
    if any(found.get(photo) != aside for photo, aside in expected.items()):
        raise DecisionsError(
            _("The decisions file does not hold your choice: try again.")
        )
    entries = tuple(entry for entry in proof.entries if entry.photo in expected)
    return proof.model_copy(update={"entries": entries})
