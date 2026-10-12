"""The `near` decisions of `review --near` in the decisions file, read back from disk.

The page never trusts its own memory: after each choice the file is read again from the
disk, and the page shows what it found there.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.plan.near_review import NearAction
from media_hygiene.report.near_decisions import NearGroupDecision
from media_hygiene.review.session_file import stamped_decisions

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.plan.similar_models import NearDecision

_FROZEN = ConfigDict(frozen=True, extra="forbid")

type GroupKey = tuple[str, tuple[str, ...]]


class NearDiskEntry(BaseModel):
    """One decided group as the decisions file holds it on the disk."""

    model_config = _FROZEN

    group: int
    action: NearAction
    keep: str = ""


class NearProof(BaseModel):
    """The decisions file as just read from the disk: when written, how big, what."""

    model_config = _FROZEN

    size: int
    modified: str  # ISO 8601, UTC: the page shows it in local time
    entries: tuple[NearDiskEntry, ...]


def group_key(mapper: HostPathMapper, group: NearDecision) -> GroupKey:
    """Name a group as the decisions file does: its kept version and its copies.

    Args:
        mapper: Container to host path translator.
        group: The group, as the audit plans it.

    Returns:
        The kept version's host path and the copies' sorted host paths.
    """
    copies = sorted(mapper.to_host(file.path) for file in group.removable)
    return mapper.to_host(group.keeper.path), tuple(copies)


def decision_key(decision: NearGroupDecision) -> GroupKey:
    """Name a decided group the way `group_key` names the groups of the audit.

    Args:
        decision: The decision, as the file holds it.

    Returns:
        Its kept version and its sorted copies.
    """
    return decision.kept, tuple(sorted(decision.copies))


def group_decision(
    mapper: HostPathMapper, group: NearDecision, action: NearAction
) -> NearGroupDecision:
    """Write one decision as the decisions file holds it.

    A swap keeps the first copy: the one the page shows next to the kept version.

    Args:
        mapper: Container to host path translator.
        group: The group, as the audit plans it.
        action: The decision.

    Returns:
        The decision, in host paths.
    """
    kept, copies = group_key(mapper, group)
    swap = action is NearAction.SWAP
    keep = mapper.to_host(group.removable[0].path) if swap else ""
    return NearGroupDecision(kept=kept, copies=copies, action=action, keep=keep)


def read_near_back(target: Path, keys: Mapping[GroupKey, int]) -> NearProof:
    """Read the decisions file from the disk, each decision placed in its group.

    Args:
        target: The decisions file, in the container.
        keys: Every group of the audit, by its key.

    Returns:
        What the file holds; decisions matching no group of the audit are left out.

    Raises:
        DecisionsError: The file cannot be read, or is not a decisions file.
    """
    decisions, (size, modified) = stamped_decisions(target)
    return NearProof(
        size=size,
        modified=modified,
        entries=tuple(
            NearDiskEntry(group=keys[key], action=decision.action, keep=decision.keep)
            for decision in decisions.near
            if (key := decision_key(decision)) in keys
        ),
    )


def near_proven(
    proof: NearProof, expected: Mapping[int, NearAction | None]
) -> NearProof:
    """Check that the file read back holds the choices just saved.

    Args:
        proof: The file, read back from the disk.
        expected: The choices, by group rank (None: undecided, so absent).

    Returns:
        The proof, reduced to those groups.

    Raises:
        DecisionsError: The file does not hold one of the choices.
    """
    found = {entry.group: entry.action for entry in proof.entries}
    if any(found.get(group) != action for group, action in expected.items()):
        raise DecisionsError(
            _("The decisions file does not hold your choice: try again.")
        )
    entries = tuple(entry for entry in proof.entries if entry.group in expected)
    return proof.model_copy(update={"entries": entries})
