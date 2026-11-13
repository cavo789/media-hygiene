"""Find the faces of one photo in a worker process; the models load once per process.

A job carries a recipe, not the models: a recipe is small and travels to the worker,
which builds the finder the first time and keeps it for the next photos. The ONNX
recipe names the two model files; the tests send a fake one.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING, Protocol, override

from media_hygiene.faces.detect import MIN_SCORE
from media_hygiene.faces.engine import FaceEngine
from media_hygiene.faces.models import PhotoFaces
from media_hygiene.faces.onnx_runner import onnx_runner
from media_hygiene.faces.straighten import worth_guessing
from media_hygiene.faces.turn_guess import NO_TURN, Seen, candidate_of, turn_of
from media_hygiene.report.thumbnails import unreadable_errors, upright_picture
from media_hygiene.scan.degree_tags import DEGREE_TURNS
from media_hygiene.scan.image_check import prepare_image_worker

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.faces.engine import FaceFinder


class FinderRecipe(Protocol):
    """How a worker builds its face finder: hashable, built once per process."""

    @override
    def __hash__(self) -> int:
        """Hash the recipe: equal recipes share one finder."""

    def build(self) -> FaceFinder:
        """Load the models."""


@dataclass(frozen=True, slots=True)
class OnnxRecipe:
    """YuNet and SFace, run by the ONNX runtime."""

    detector: Path
    embedder: Path
    least: float = MIN_SCORE  # the lowest score of a face kept (lower: a second look)

    def build(self) -> FaceFinder:
        """Load both model files.

        Returns:
            The engine.
        """
        detector, embedder = onnx_runner(self.detector), onnx_runner(self.embedder)
        return FaceEngine(detector, embedder, self.least)


@dataclass(frozen=True, slots=True)
class FaceJob:
    """One version of a photo, and the recipe of the finder."""

    path: Path
    size: int
    mtime_ns: int
    recipe: FinderRecipe
    turn_only: bool = False  # faces kept already: only the turn is guessed (0725)


def find_faces(job: FaceJob) -> PhotoFaces | None:
    """Decode a photo upright, find its faces and guess its turn.

    A turn-only job whose photo is not worth guessing is answered from its header,
    without decoding it, and without faces (`complete` False). A photo tagged in
    degrees is analysed whole again: its faces were found sideways before 0724.

    Args:
        job: The photo and the recipe.

    Returns:
        Its faces, the time taken (decoding included) and its turn; None when
        undecodable.
    """
    prepare_image_worker()
    started = time.monotonic()
    if job.turn_only:
        candidate = candidate_of(job.path)
        if candidate is None or not (
            worth_guessing(candidate) or candidate.orientation in DEGREE_TURNS
        ):
            return PhotoFaces(
                job.path, job.size, job.mtime_ns, (), 0.0, NO_TURN, complete=False
            )
    finder = finder_of(job.recipe)
    try:
        picture = upright_picture(job.path)
    except unreadable_errors():
        return None
    faces = finder.find(picture)
    turn = turn_of(Seen(job.path, picture, len(faces)), finder)
    seconds = time.monotonic() - started
    return PhotoFaces(job.path, job.size, job.mtime_ns, faces, seconds, turn)


@cache
def finder_of(recipe: FinderRecipe) -> FaceFinder:
    """Build the finder of a recipe once per process.

    Args:
        recipe: The recipe.

    Returns:
        The finder.
    """
    return recipe.build()
