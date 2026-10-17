"""The `gone` answers of `review --gone` in the decisions file, read back.

The page never trusts its own memory: after each answer the file is read again from the
disk, and the page shows what it found there.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.review.session_file import stamped_decisions

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

_FROZEN = ConfigDict(frozen=True, extra="forbid")

# A file gone, as the decisions file names it: host path, size, modification time.
type FileKey = tuple[str, int, int]


class GoneDiskEntry(BaseModel):
    """One answer as the decisions file holds it on the disk."""

    model_config = _FROZEN

    file: int
    deleted: bool


class GoneProof(BaseModel):
    """The decisions file as just read from the disk: when written, how big, what."""

    model_config = _FROZEN

    size: int
    modified: str  # ISO 8601, UTC: the page shows it in local time
    entries: tuple[GoneDiskEntry, ...]


def read_gone_back(target: Path, keys: Mapping[FileKey, int]) -> GoneProof:
    """Read the decisions file from the disk, each answer placed on its file.

    Args:
        target: The decisions file, in the container.
        keys: Every file of the review, by its key.

    Returns:
        What the file holds; answers matching no file are left out.

    Raises:
        DecisionsError: The file cannot be read, or is not a decisions file.
    """
    decisions, (size, modified) = stamped_decisions(target)
    entries = (
        GoneDiskEntry(file=rank, deleted=entry.deleted)
        for entry in decisions.gone
        if (rank := keys.get((entry.path, entry.size, entry.mtime_ns))) is not None
    )
    return GoneProof(size=size, modified=modified, entries=tuple(entries))


def gone_proven(proof: GoneProof, expected: Mapping[int, bool | None]) -> GoneProof:
    """Check that the file read back holds the answers just saved.

    Args:
        proof: The file, read back from the disk.
        expected: The answers, by file rank (None: unanswered, so absent).

    Returns:
        The proof, reduced to those files.

    Raises:
        DecisionsError: The file does not hold one of the answers.
    """
    found = {entry.file: entry.deleted for entry in proof.entries}
    if any(found.get(rank) != deleted for rank, deleted in expected.items()):
        raise DecisionsError(
            _("The decisions file does not hold your choice: try again.")
        )
    entries = tuple(entry for entry in proof.entries if entry.file in expected)
    return proof.model_copy(update={"entries": entries})
