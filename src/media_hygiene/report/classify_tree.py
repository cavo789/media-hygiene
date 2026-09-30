"""The proposed tree: the target folders and their file counts, before any move."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from media_hygiene.classify.plan_file import ClassifyPlan


@dataclass(frozen=True, slots=True)
class TreeLine:
    """One folder of the proposed tree and the files it will hold, below it included."""

    depth: int
    name: str
    files: int


def proposed_tree(plan: ClassifyPlan) -> list[TreeLine]:
    """The target folders and their file counts: the collection once sorted.

    Args:
        plan: The plan.

    Returns:
        One line per folder, parents first; the files that stay are not in it.
    """
    counts: Counter[tuple[str, ...]] = Counter()
    for row in plan.rows:
        if row.folder is None:
            continue
        parts = (row.root, *row.folder.split("/"))
        for depth in range(1, len(parts) + 1):
            counts[parts[:depth]] += 1
    return [
        TreeLine(len(parts) - 1, parts[-1], files)
        for parts, files in sorted(counts.items())
    ]
