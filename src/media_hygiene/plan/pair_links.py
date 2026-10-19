"""A folder pair keeping both names: each copy a hard link to its kept file (0213).

A hard link is one file under two names: the copy's bytes are freed, both folders still
show the photo. It cannot cross a drive, nor leave a protected folder's file editable
from elsewhere: an edit saved in place through one name shows under the other.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.constants import KeepReason
from media_hygiene.i18n import _
from media_hygiene.paths.host_paths import is_within

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.plan.models import CleanPlan
    from media_hygiene.plan.pairs import Copy, FolderPair

_DRIVE: Final = 2  # "E:"


def link_refusal(
    pair: FolderPair, mapper: HostPathMapper, protected: Iterable[Path] = ()
) -> str | None:
    """Tell why the copies of a pair cannot become links to their kept files.

    Args:
        pair: The folder pair, as the audit plans it.
        mapper: Container to host path translator (the drive letters).
        protected: The protected folders, in container paths.

    Returns:
        The translated reason, or None when every copy may be linked.
    """
    kept_in = mapper.to_host(pair.kept_in)
    if _drive(kept_in) != _drive(mapper.to_host(pair.removed_from)):
        return _("the two folders are on two drives: a hard link cannot cross them")
    if not all(_same_device(copy) for copy in pair.copies):
        return _(
            "the two folders are on two disks or two mounts: a hard link cannot "
            "cross them"
        )
    in_protected = any(is_within(pair.kept_in, folder) for folder in protected)
    if in_protected or any(c.reason is KeepReason.PROTECTED for c in pair.copies):
        return _(
            "{folder} is protected: a link would let an edit made through the other "
            "name change it"
        ).format(folder=kept_in)
    return None


def linked_count(plan: CleanPlan) -> int:
    """Count the copies a clean replaces by a link to their kept file.

    Args:
        plan: What would be cleaned.

    Returns:
        The count.
    """
    return sum(len(decision.linked) for decision in plan.decisions)


def linked_size(plan: CleanPlan) -> int:
    """Bytes freed by replacing copies by links to their kept files.

    Args:
        plan: What would be cleaned.

    Returns:
        The byte count.
    """
    return sum(decision.size * len(decision.linked) for decision in plan.decisions)


def _same_device(copy: Copy) -> bool:
    """Tell whether a copy and its kept file lay on one filesystem when listed.

    Args:
        copy: The copy and its kept file.

    Returns:
        False when either identity is unknown, or the devices differ.
    """
    kept, removed = copy.kept.identity, copy.removed.identity
    return kept is not None and removed is not None and kept.device == removed.device


def _drive(host_path: str) -> str | None:
    r"""The drive letter of a host path.

    Args:
        host_path: A path as the user knows it (`E:\Photos`, `/home/me`).

    Returns:
        `E:`, or None for a path without a drive letter.
    """
    drive = host_path[:_DRIVE].upper()
    return drive if drive.endswith(":") else None
