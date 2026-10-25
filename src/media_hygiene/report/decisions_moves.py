"""`decisions.json` follows the files `sort` or `undo` moved (0382).

The burst series, the near duplicates, the files chosen in `search`, the unwanted and
the gone ones name files by their host path: each one moved is renamed in place, its
size and date kept (a move changes neither). The folder pairs name folders: a pair
whose folder no longer exists is dropped, and counted. `roots` gain the folder a moved
file went to when none of them holds it, so that `clean --decisions` still accepts the
file. The file is saved at once, then read back from the disk.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.report.decisions import read_decisions, write_decisions
from media_hygiene.report.decisions_paths import inside, paths_of, renamed

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path

    from media_hygiene.report.decisions import DecisionsFile


@dataclass(frozen=True, slots=True)
class DecisionMoves:
    """The moves of a run in host paths, and how to tell a folder still exists."""

    moves: Mapping[str, str]  # new host path by old one
    roots: Mapping[str, str]  # the host root each new path went into
    exists: Callable[[str], bool]  # a host folder is there


@dataclass(frozen=True, slots=True)
class DecisionsFollowed:
    """What changed in the file, read back from the disk."""

    paths: int  # file paths renamed
    pairs_dropped: int  # folder pairs whose folder is gone


def follow_decisions(path: Path, moved: DecisionMoves) -> DecisionsFollowed:
    """Rename the moved files of a decisions file, drop the pairs of folders gone.

    Args:
        path: `decisions.json`, in the container; missing: nothing to do.
        moved: The moves of the run.

    Returns:
        What changed, counted on the file read back.

    Raises:
        DecisionsError: The file is not a decisions file.
        OSError: It cannot be written.
    """
    if not path.is_file():
        return DecisionsFollowed(0, 0)
    before = read_decisions(path)
    after = _followed(before, moved)
    if after == before:
        return DecisionsFollowed(0, 0)
    write_decisions(path, after)
    back = read_decisions(path)
    count = sum(1 for old in paths_of(before) if old in moved.moves)
    return DecisionsFollowed(count, len(before.pairs) - len(back.pairs))


def _followed(decisions: DecisionsFile, moved: DecisionMoves) -> DecisionsFile:
    """The decisions with every moved path renamed.

    Args:
        decisions: As read.
        moved: The moves.

    Returns:
        The decisions to save.
    """

    def one(path: str) -> str:
        """One path, renamed when its file moved.

        Args:
            path: A host path.

        Returns:
            Where the file is now.
        """
        return moved.moves.get(path, path)

    def many(paths: tuple[str, ...]) -> tuple[str, ...]:
        """Several paths, renamed, each once.

        Args:
            paths: Host paths.

        Returns:
            Them, renamed.
        """
        return tuple(dict.fromkeys(one(path) for path in paths))

    bursts = tuple(
        burst.model_copy(
            update={"kept": many(burst.kept), "discarded": many(burst.discarded)}
        )
        for burst in decisions.bursts
    )
    near = tuple(
        group.model_copy(
            update={
                "kept": one(group.kept),
                "copies": many(group.copies),
                "keep": one(group.keep) if group.keep else "",
            }
        )
        for group in decisions.near
    )
    pairs = tuple(
        pair
        for pair in decisions.pairs
        if moved.exists(pair.kept_in) and moved.exists(pair.removed_from)
    )
    return decisions.model_copy(
        update={
            "roots": _roots(decisions, moved),
            "pairs": pairs,
            "bursts": bursts,
            "near": near,
            "chosen": renamed(decisions.chosen, one),
            "unwanted": renamed(decisions.unwanted, one),
            "gone": renamed(decisions.gone, one),
        }
    )


def _roots(decisions: DecisionsFile, moved: DecisionMoves) -> tuple[str, ...]:
    """The roots, with the root of each destination none of them holds.

    Args:
        decisions: As read.
        moved: The moves.

    Returns:
        The roots, each once.
    """
    roots = list(decisions.roots)
    used = {
        moved.roots[new] for old in paths_of(decisions) if (new := moved.moves.get(old))
    }
    for root in sorted(used):
        if not any(inside(root, known) for known in roots):
            roots.append(root)
    return tuple(roots)
