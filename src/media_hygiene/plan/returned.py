"""Files set aside by a choice that came back (a phone backup): proposed again (0216).

A burst shot, a near duplicate, a file chosen in `search` or an unwanted photo set
aside is remembered by its content (size, SHA-256) in the journals; a file of the
same content found again, whatever its name, is "back after being set aside".
`clean` moves it to the quarantine again, with the rest of its plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from datetime import datetime
    from pathlib import Path

    from media_hygiene.actions.kinds import ActionKind
    from media_hygiene.plan.keeper import KeepPolicy
    from media_hygiene.plan.models import CleanPlan
    from media_hygiene.scan.models import MediaFile

# A content: its size, then its SHA-256 (or partial digest, `by_partial`).
type ContentKey = tuple[int, str]


@dataclass(frozen=True, slots=True)
class Remembered:
    """A content set aside: by which run, when, why, and where it lay (on the host)."""

    run_id: str
    at: datetime
    action: ActionKind
    host_path: str


@dataclass(frozen=True, slots=True)
class JournalWord:
    """What one journal says of a content: set aside (`said`), or restored (None).

    `partial`: the key holds the partial digest, not the SHA-256 (a gone file, 0224).
    """

    at: datetime
    key: ContentKey
    said: Remembered | None = None
    partial: bool = False


def _empty() -> Mapping[ContentKey, Remembered]:
    """An empty, read-only mapping.

    Returns:
        It.
    """
    return MappingProxyType({})


@dataclass(frozen=True, slots=True)
class RememberedSet:
    """Every content set aside and not restored since, by SHA-256 or partial digest.

    `by_partial` holds the contents known by their partial digest only (0224).
    """

    by_digest: Mapping[ContentKey, Remembered] = field(default_factory=_empty)
    by_partial: Mapping[ContentKey, Remembered] = field(default_factory=_empty)

    @property
    def digest_sizes(self) -> frozenset[int]:
        """The sizes a file must have to be hashed in full and compared.

        Returns:
            Them.
        """
        return frozenset(size for size, _digest in self.by_digest)

    @property
    def partial_sizes(self) -> frozenset[int]:
        """The sizes whose partial digest is compared.

        Returns:
            Them.
        """
        return frozenset(size for size, _digest in self.by_partial)

    def __len__(self) -> int:
        """Count the contents remembered.

        Returns:
            The count.
        """
        return len(self.by_digest) + len(self.by_partial)


@dataclass(frozen=True, slots=True)
class ReturnedFile:
    """A file found again with the content of one set aside, and its digests.

    `digest` is the SHA-256 remembered (None: matched on the partial digest only).
    """

    file: MediaFile
    remembered: Remembered
    digest: str | None = None
    partial: str | None = None


def in_plan(
    returned: Iterable[ReturnedFile], plan: CleanPlan, policy: KeepPolicy
) -> tuple[ReturnedFile, ...]:
    """Keep the files `clean` may move: not protected, not removed as a copy already.

    Args:
        returned: The files found again.
        plan: The audit's plan (its exact copies are moved as copies).
        policy: Tells the protected folders apart: never modified.

    Returns:
        The files back, by path.
    """
    copies = {file.path for group in plan.decisions for file in group.removable}
    kept = (
        item
        for item in returned
        if item.file.path not in copies and not policy.is_protected(item.file)
    )
    return tuple(sorted(kept, key=lambda item: str(item.file.path)))


def returned_moves(plan: CleanPlan) -> tuple[ReturnedFile, ...]:
    """The files back that nothing else of the plan removes (a near tier, a review).

    Args:
        plan: What to clean.

    Returns:
        The files `clean` moves as `quarantine-returned`.
    """
    if not plan.returned:
        return ()
    taken = _others(plan)
    return tuple(item for item in plan.returned if item.file.path not in taken)


def returned_size(plan: CleanPlan) -> int:
    """Weigh the files back that `clean` moves.

    Args:
        plan: What to clean.

    Returns:
        Their bytes.
    """
    return sum(item.file.size for item in returned_moves(plan))


def _others(plan: CleanPlan) -> set[Path]:
    """The files the rest of the plan removes.

    Args:
        plan: What to clean.

    Returns:
        Their paths.
    """
    files = (
        *(file for group in plan.decisions for file in group.removable),
        *(file for group in plan.near for file in group.removable),
        *(file for choice in plan.bursts for file in choice.discarded),
        *plan.chosen,
        *plan.unwanted,
        *(item.file for item in plan.broken),
    )
    return {file.path for file in files}
