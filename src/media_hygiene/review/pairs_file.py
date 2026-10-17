"""The `pairs` decisions of `review --pairs` in the decisions file, read back from disk.

The same `pairs` key the report's download writes (`PairDecision`); the page never
trusts its own memory: after each choice the file is read again from the disk, and the
page shows what it found there.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.plan.review import PairAction
from media_hygiene.report.decisions import PairDecision
from media_hygiene.review.session_file import stamped_decisions

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.plan.pairs import FolderPair

_FROZEN = ConfigDict(frozen=True, extra="forbid")

type PairKey = tuple[str, str]


class PairDiskEntry(BaseModel):
    """One decided pair as the decisions file holds it on the disk."""

    model_config = _FROZEN

    pair: int
    action: PairAction


class PairsProof(BaseModel):
    """The decisions file as just read from the disk: when written, how big, what."""

    model_config = _FROZEN

    size: int
    modified: str  # ISO 8601, UTC: the page shows it in local time
    entries: tuple[PairDiskEntry, ...]


def pair_key(mapper: HostPathMapper, pair: FolderPair) -> PairKey:
    """Name a pair as the decisions file does: its two folders, in host paths.

    Args:
        mapper: Container to host path translator.
        pair: The folder pair, as the audit plans it.

    Returns:
        The folder keeping the copies, and the folder losing them.
    """
    return mapper.to_host(pair.kept_in), mapper.to_host(pair.removed_from)


def pair_decision(key: PairKey, action: PairAction) -> PairDecision:
    """Write one decision as the decisions file holds it.

    Args:
        key: The pair's folders, in host paths.
        action: The decision.

    Returns:
        The decision.
    """
    kept_in, removed_from = key
    return PairDecision(kept_in=kept_in, removed_from=removed_from, action=action)


def read_pairs_back(target: Path, keys: Mapping[PairKey, int]) -> PairsProof:
    """Read the decisions file from the disk, each decision placed on its pair.

    Args:
        target: The decisions file, in the container.
        keys: Every pair of the audit, by its key.

    Returns:
        What the file holds; decisions matching no pair of the audit are left out.

    Raises:
        DecisionsError: The file cannot be read, or is not a decisions file.
    """
    decisions, (size, modified) = stamped_decisions(target)
    return PairsProof(
        size=size,
        modified=modified,
        entries=tuple(
            PairDiskEntry(pair=keys[key], action=decision.action)
            for decision in decisions.pairs
            if (key := (decision.kept_in, decision.removed_from)) in keys
        ),
    )


def pairs_proven(
    proof: PairsProof, expected: Mapping[int, PairAction | None]
) -> PairsProof:
    """Check that the file read back holds the choices just saved.

    Args:
        proof: The file, read back from the disk.
        expected: The choices, by pair rank (None: undecided, so absent).

    Returns:
        The proof, reduced to those pairs.

    Raises:
        DecisionsError: The file does not hold one of the choices.
    """
    found = {entry.pair: entry.action for entry in proof.entries}
    if any(found.get(pair) != action for pair, action in expected.items()):
        raise DecisionsError(
            _("The decisions file does not hold your choice: try again.")
        )
    entries = tuple(entry for entry in proof.entries if entry.pair in expected)
    return proof.model_copy(update={"entries": entries})
