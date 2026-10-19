"""From the vectors to what the pages show: best pictures per search, closest pairs.

A pair the audit already calls a near duplicate is left out of the pairs: its dHash and
pHash differ by at most `NEAR_DISTANCE` bits (the audit's own test; it also asks for the
same proportions and date, so a few pairs left out here would not be grouped by it: the
page errs towards showing only what the hashes miss). Today's `search` answers come from
the index when one is mounted: the same words, among the sampled photos only.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from itertools import combinations
from typing import TYPE_CHECKING, Final

import numpy as np
from PIL import UnidentifiedImageError

from media_hygiene.plan.likeness import distance
from media_hygiene.plan.near import NEAR_DISTANCE
from media_hygiene.scan.visual import dhash, phash
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.query import SearchQuery, parse_terms

from .runs import open_upright, readers

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from numpy.typing import NDArray

    from .runs import ModelRun

SHOWN: Final = 24  # pictures per search and model
PAIRS: Final = 50  # closest pairs per model
_EVERY_MATCH: Final = 1_000_000  # `search` answers read before keeping the sampled ones
SEARCH: Final = "search"  # the column of today's search, beside the models


@dataclass(frozen=True, slots=True)
class Bench:
    """Everything measured: photos, searches, each model's run, today's answers."""

    photos: tuple[Path, ...]
    queries: tuple[str, ...]
    runs: tuple[ModelRun, ...]
    search: tuple[tuple[int, ...], ...] | None  # per search, photo numbers best first


@dataclass(frozen=True, slots=True)
class Pair:
    """Two photos a model finds alike."""

    first: int
    second: int
    similarity: float


@dataclass(frozen=True, slots=True)
class Ranked:
    """What the pages show."""

    bench: Bench
    answers: tuple[dict[str, tuple[int, ...]], ...]  # per search: column -> photos
    pairs: dict[str, tuple[Pair, ...]]  # per model


def best(texts: NDArray[np.float32], run: ModelRun) -> tuple[tuple[int, ...], ...]:
    """The photos closest to each search, the unreadable ones left out.

    Args:
        texts: One unit vector per search.
        run: The model's photo vectors.

    Returns:
        Per search, at most `SHOWN` photo numbers, closest first.
    """
    scores = texts @ run.images.T
    scores[:, ~run.readable] = -np.inf
    readable = int(run.readable.sum())
    order = np.argsort(-scores, axis=1, kind="stable")[:, : min(SHOWN, readable)]
    return tuple(tuple(int(index) for index in row) for row in order)


def hashes_of(photos: Sequence[Path]) -> tuple[tuple[int, int] | None, ...]:
    """The audit's two perceptual hashes of each photo.

    Args:
        photos: The photos.

    Returns:
        Per photo, its dHash and pHash, None when it cannot be read.
    """
    readers()
    found: list[tuple[int, int] | None] = []
    for path in photos:
        try:
            gray = open_upright(path).convert("L")
        except OSError, UnidentifiedImageError, ValueError:
            found.append(None)
            continue
        found.append((dhash(gray), phash(gray)))
    return tuple(found)


def near_pairs(hashes: Sequence[tuple[int, int] | None]) -> frozenset[tuple[int, int]]:
    """The pairs whose hashes the audit's near-duplicate test accepts.

    Args:
        hashes: Per photo, its dHash and pHash, or None.

    Returns:
        The pairs `(i, j)`, `i < j`.
    """
    known = [(index, pair) for index, pair in enumerate(hashes) if pair is not None]
    return frozenset(
        (first, second)
        for (first, (d1, p1)), (second, (d2, p2)) in combinations(known, 2)
        if distance(d1, d2) <= NEAR_DISTANCE and distance(p1, p2) <= NEAR_DISTANCE
    )


def closest_pairs(run: ModelRun, near: frozenset[tuple[int, int]]) -> tuple[Pair, ...]:
    """The pairs of photos a model finds the most alike, near duplicates left out.

    Args:
        run: The model's photo vectors.
        near: The pairs the audit already finds.

    Returns:
        At most `PAIRS` pairs, the most alike first.
    """
    similarity = run.images @ run.images.T
    firsts, seconds = np.triu_indices(len(run.images), k=1)
    both = run.readable[firsts] & run.readable[seconds]
    firsts, seconds = firsts[both], seconds[both]
    values = similarity[firsts, seconds]
    found: list[Pair] = []
    for at in np.argsort(-values, kind="stable"):
        key = (int(firsts[at]), int(seconds[at]))
        if key not in near:
            found.append(Pair(key[0], key[1], float(values[at])))
        if len(found) == PAIRS:
            break
    return tuple(found)


def search_hits(
    index: Path, queries: Sequence[str], photos: Sequence[Path]
) -> tuple[tuple[int, ...], ...] | None:
    """Today's `search` answers among the sampled photos, when an index is there.

    The photos must be mounted where the audit saw them (`/data/c/Photos`): the
    index knows them by that path.

    Args:
        index: The index file.
        queries: The searches.
        photos: The sampled photos.

    Returns:
        Per search, at most `SHOWN` photo numbers best first; None without an index.
    """
    if not index.is_file():
        return None
    number = {str(path): at for at, path in enumerate(photos)}
    answers: list[tuple[int, ...]] = []
    try:
        with SearchIndex.open(index) as search:
            for query in queries:
                found = search.find(SearchQuery(parse_terms(query)), _EVERY_MATCH)
                hits = (number.get(str(hit.photo.path)) for hit in found.hits)
                answers.append(tuple(at for at in hits if at is not None)[:SHOWN])
    except sqlite3.Error:
        return None
    return tuple(answers)


def ranked(bench: Bench) -> Ranked:
    """Rank every model's answers and pairs.

    Args:
        bench: What was measured.

    Returns:
        What the pages show.
    """
    per_model = {
        run.model: best(run.texts, run) for run in bench.runs if run.texts is not None
    }
    answers: list[dict[str, tuple[int, ...]]] = []
    for at in range(len(bench.queries)):
        columns = {model: rows[at] for model, rows in per_model.items()}
        if bench.search is not None:
            columns[SEARCH] = bench.search[at]
        answers.append(columns)
    near = near_pairs(hashes_of(bench.photos))
    pairs = {run.model: closest_pairs(run, near) for run in bench.runs}
    return Ranked(bench, tuple(answers), pairs)
