"""The decisions file of a review: every series listed, and each choice read back.

The page never trusts its own memory: after each choice the file is read again from the
disk, and the page shows what it found there.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.report.decisions import BurstDecision, BurstStatus, read_decisions
from media_hygiene.review.shots import burst_decision, match_burst, set_aside_problem

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.review.session import ReviewSource
    from media_hygiene.review.shots import ShotPlace
    from media_hygiene.scan.models import MediaFile

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_NANOSECONDS: Final = 1_000_000_000


class DiskEntry(BaseModel):
    """One series as the decisions file holds it on the disk."""

    model_config = _FROZEN

    series: int
    status: BurstStatus
    kept: tuple[str, ...]
    discarded: tuple[str, ...]


class FileProof(BaseModel):
    """The decisions file as just read from the disk: when written, how big, what."""

    model_config = _FROZEN

    size: int
    modified: str  # ISO 8601, UTC: the page shows it in local time
    entries: tuple[DiskEntry, ...]


def series_decision(
    mapper: HostPathMapper,
    shots: tuple[MediaFile, ...],
    discarded: frozenset[int] | None,
) -> BurstDecision:
    """Write one series as the decisions file holds it.

    Args:
        mapper: Container to host path translator.
        shots: The shots of the series.
        discarded: Ranks of the shots set aside; None for a series not seen yet.

    Returns:
        The decision, in host paths: `todo` with every shot kept when not seen.
    """
    if discarded is None:
        return burst_decision(mapper, shots, frozenset()).model_copy(
            update={"status": BurstStatus.TODO}
        )
    return burst_decision(mapper, shots, discarded)


def read_back(target: Path, places: Mapping[str, ShotPlace]) -> FileProof:
    """Read the decisions file from the disk, each entry placed in its series.

    Args:
        target: The decisions file, in the container.
        places: Every shot of the audit, from `shot_places`.

    Returns:
        What the file holds; entries matching no series of the audit are left out.

    Raises:
        DecisionsError: The file cannot be read, or is not a decisions file.
    """
    decisions = read_decisions(target)
    try:
        written = target.stat()
    except OSError as exc:
        message = _("Cannot read the decisions file {path}.").format(path=target)
        raise DecisionsError(message) from exc
    entries = (
        (decision, match_burst(decision, places)) for decision in decisions.bursts
    )
    modified = datetime.fromtimestamp(written.st_mtime_ns / _NANOSECONDS, tz=UTC)
    return FileProof(
        size=written.st_size,
        modified=modified.isoformat(),
        entries=tuple(
            DiskEntry(
                series=match.series,
                status=decision.status,
                kept=decision.kept,
                discarded=decision.discarded,
            )
            for decision, match in entries
            if match is not None
        ),
    )


def proven(proof: FileProof, expected: Mapping[int, BurstDecision]) -> FileProof:
    """Check that the file read back holds the choices just saved.

    Args:
        proof: The file, read back from the disk.
        expected: The choices, as they were written, by series rank.

    Returns:
        The proof, reduced to those series.

    Raises:
        DecisionsError: The file does not hold one of the choices.
    """
    found = [entry for entry in proof.entries if entry.series in expected]
    held = {entry.series: (entry.status, sorted(entry.discarded)) for entry in found}
    wanted = {
        series: (decision.status, sorted(decision.discarded))
        for series, decision in expected.items()
    }
    if len(found) != len(expected) or held != wanted:
        raise DecisionsError(
            _("The decisions file does not hold your choice: try again.")
        )
    return proof.model_copy(update={"entries": tuple(found)})


def choice_problem(
    source: ReviewSource, series: int, discarded: frozenset[int] | None
) -> str | None:
    """Explain why a choice cannot be made on a series, or return None.

    Args:
        source: The series of the review.
        series: Rank of the series.
        discarded: Ranks of the shots to set aside (None: back to still to see).

    Returns:
        The translated reason, or None.
    """
    if not 0 <= series < len(source.bursts):
        return _("There is no such series.")
    shots = source.bursts[series].shots
    return set_aside_problem(source.builder, shots, discarded or frozenset())
