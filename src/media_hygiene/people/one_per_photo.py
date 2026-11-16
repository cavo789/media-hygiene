"""A person is on a photo once: the guesses of a photo's faces, in cascade.

A name confirmed on a face of a photo is never guessed for another face of it; two
faces guessed the same name keep it for the closer one, and the other takes its next
closest name still free, if close enough (2026-11-16: ✓ Valéry and ≈ Valéry side by
side on one photo).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from pathlib import Path

    from numpy.typing import NDArray

    from media_hygiene.index.face_rows import StoredFace
    from media_hygiene.people.known import Known
    from media_hygiene.people.naming import FaceName


@dataclass(frozen=True, slots=True)
class Guess:
    """A face to guess: its row, its photo, its likeness to each reference."""

    row: int
    path: Path
    scores: NDArray[np.float32]


def taken_names(
    faces: Sequence[StoredFace], names: Sequence[FaceName | None]
) -> dict[Path, set[str]]:
    """The names already given on each photo (confirmed).

    Args:
        faces: The block's faces.
        names: Their names so far, None for those left to guess.

    Returns:
        Per photo, the names its faces bear.
    """
    taken: dict[Path, set[str]] = defaultdict(set)
    for face, name in zip(faces, names, strict=True):
        if name is not None and name.named:
            taken[face.path].add(name.name)
    return taken


def once_per_photo(
    guesses: Sequence[Guess], known: Known, taken: dict[Path, set[str]]
) -> Iterator[tuple[int, int | None]]:
    """Guess each face a name not yet on its photo, the closest faces first.

    Args:
        guesses: The faces to guess.
        known: The references.
        taken: Per photo, the names given (completed as names are guessed).

    Yields:
        The row of each face and its reference column, None when none is close enough.
    """
    columns = np.array(known.names, dtype=object)
    for guess in sorted(guesses, key=lambda one: -float(np.max(one.scores))):
        used = taken.setdefault(guess.path, set())
        scores = np.where(np.isin(columns, list(used)), -1.0, guess.scores)
        best = int(np.argmax(scores))
        if scores[best] < known.rule.similarity:
            yield guess.row, None
            continue
        if known.names[best]:
            used.add(known.names[best])
        yield guess.row, best
