"""Rank photos by what they show: the search's vector against the photos' vectors.

The text model loads at the first search by meaning (about a second, measured by the
bench: 0.9 s), and a search typed again reuses its vector. A model that cannot load
(a build without `tokenizers`, a file missing) leaves the words alone: the search
never fails for it. The photos' vectors are read from the index once per change of
the index, as the full-text table is.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.errors import FaceModelError
from media_hygiene.index.meaning_rows import vectors
from media_hygiene.meaning.clip import MODEL

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Callable, Collection, Sequence

    from numpy.typing import NDArray

    from media_hygiene.meaning.embedder import TextReader

# Reciprocal rank fusion: each list gives a file 1 / (K + its rank). 60 is the
# constant of the method's paper (Cormack et al., 2009), never tuned here.
RRF_K: Final = 60


@dataclass(frozen=True, slots=True)
class MeaningSource:
    """How to load the text model, and how many photos a search finds at most."""

    load: Callable[[], TextReader]
    results: int


class Meaning:
    """The text model, loaded once, and the photos' vectors, read once per change."""

    def __init__(self, source: MeaningSource) -> None:
        """Keep the way to load the model; nothing loads yet.

        Args:
            source: The loader and the number of results.
        """
        self._source = source
        self._reader: TextReader | None = None
        self._broken = False
        self._texts: dict[str, NDArray[np.float32]] = {}
        self._keys: tuple[int, ...] = ()
        self._matrix: NDArray[np.float32] = np.zeros((0, 0), dtype=np.float32)

    def read(self, connection: sqlite3.Connection) -> None:
        """Read the photos' vectors again (the index changed).

        Args:
            connection: The index.
        """
        self._keys, self._matrix = vectors(connection, MODEL)

    def closest(
        self, text: str, pool: Collection[int] | None
    ) -> tuple[int, ...] | None:
        """The photos closest to a search, the closest first.

        Args:
            text: The words to understand.
            pool: The files allowed (a name, a place, the filters); None: all.

        Returns:
            At most `results` file rows; None when the model cannot load.
        """
        query = self._vector(text)
        if query is None or not self._keys:
            return None if query is None else ()
        scores = self._matrix @ query
        allowed = [
            index for index, key in enumerate(self._keys) if pool is None or key in pool
        ]
        allowed.sort(key=lambda index: (-float(scores[index]), self._keys[index]))
        return tuple(self._keys[index] for index in allowed[: self._source.results])

    def _vector(self, text: str) -> NDArray[np.float32] | None:
        """The vector of a search, from the model loaded at the first one.

        Args:
            text: The words.

        Returns:
            The vector; None when the model cannot load.
        """
        if text in self._texts:
            return self._texts[text]
        if self._broken:
            return None
        if self._reader is None:
            try:
                self._reader = self._source.load()
            except FaceModelError, OSError:
                self._broken = True
                return None
        vector = self._reader.text(text)
        self._texts[text] = vector
        return vector


def fused(lists: Sequence[Sequence[int]]) -> tuple[int, ...]:
    """Merge rankings by reciprocal rank fusion.

    Args:
        lists: Each ranking, best first.

    Returns:
        Every file of any list, the best fused score first (ties: the row first).
    """
    scores: defaultdict[int, float] = defaultdict(float)
    for ranking in lists:
        for rank, key in enumerate(ranking, start=1):
            scores[key] += 1.0 / (RRF_K + rank)
    return tuple(sorted(scores, key=lambda key: (-scores[key], key)))
