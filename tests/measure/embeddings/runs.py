"""One model's run: the photos sampled, decoded and embedded, every part timed.

`run_job` runs in a process of its own (`measure.main`): the RAM peak it reads is that
model's alone. The photos are only read.
"""

from __future__ import annotations

import os
import random
import resource
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

import numpy as np
import pillow_heif
from PIL import Image, ImageOps, UnidentifiedImageError

from media_hygiene.constants import IMAGE_EXTENSIONS

from .embedders import load_embedder
from .models import SPECS, size_mb

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import NDArray

    from .embedders import Embedder

_SKIPPED_PREFIXES: Final = ("#", "@", ".")  # #recycle, @eaDir, hidden folders
_DRAFT_SIDE: Final = 512  # JPEG decoded at a reduced scale, as the audit does
_KILOBYTES_PER_MB: Final = 1024  # Linux gives `ru_maxrss` in kilobytes
_COMMENT: Final = "#"


@dataclass(frozen=True, slots=True)
class Job:
    """What one model's process does."""

    model: str
    models_dir: Path
    photos: tuple[Path, ...]
    queries: tuple[str, ...]
    threads: int


@dataclass(frozen=True, slots=True)
class Timing:  # pylint: disable=too-many-instance-attributes  # one per cost
    """What a model costs, measured in its process."""

    load_seconds: float
    decode_seconds: float  # per photo: opening and decoding the file
    model_seconds: float  # per photo: resizing and running the model
    text_seconds: float  # per search
    peak_mb: float
    model_mb: float
    threads: int
    failed: int


@dataclass(frozen=True, slots=True)
class ModelRun:
    """One model's vectors and costs."""

    model: str
    images: NDArray[
        np.float32
    ]  # one row per photo; zeros for a photo it could not read
    readable: NDArray[np.bool_]
    texts: (
        NDArray[np.float32] | None
    )  # one row per search; None: the model reads no text
    timing: Timing


def sample(folder: Path, count: int, seed: int) -> tuple[Path, ...]:
    """Pick photos at random, always the same ones for the same seed and folder.

    Args:
        folder: The photos, walked below.
        count: How many to pick (all of them when there are fewer).
        seed: The seed of the draw.

    Returns:
        The photos, sorted by path.
    """
    found: list[Path] = []
    for top, folders, files in os.walk(folder):
        folders[:] = sorted(
            name for name in folders if not name.startswith(_SKIPPED_PREFIXES)
        )
        found.extend(
            Path(top) / name
            for name in files
            if Path(name).suffix.lower() in IMAGE_EXTENSIONS
        )
    found.sort()
    if count >= len(found):
        return tuple(found)
    draw = random.Random(seed)  # noqa: S311 - a repeatable draw, not a secret
    return tuple(sorted(draw.sample(found, count)))


def read_queries(path: Path) -> tuple[str, ...]:
    """Read the searches: one per line, blank lines and `#` comments left out.

    Args:
        path: The text file (UTF-8).

    Returns:
        The searches, in order.
    """
    lines = (line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines())
    return tuple(line for line in lines if line and not line.startswith(_COMMENT))


def readers() -> None:
    """Read HEIC photos, and huge panoramas, as the audit does."""
    pillow_heif.register_heif_opener()
    Image.MAX_IMAGE_PIXELS = None


def open_upright(path: Path) -> Image.Image:
    """Decode a photo, at a reduced scale when the format allows, turned upright.

    Args:
        path: The photo.

    Returns:
        The decoded picture.
    """
    with Image.open(path) as image:
        image.draft("RGB", (_DRAFT_SIDE, _DRAFT_SIDE))
        image.load()
        return ImageOps.exif_transpose(image)


def run_job(job: Job) -> ModelRun:
    """Embed every photo and search with one model, timing each part.

    Args:
        job: The model and what to embed.

    Returns:
        Its vectors and costs.
    """
    readers()
    started = time.perf_counter()
    model = load_embedder(job.model, job.models_dir, job.threads)
    load_seconds = time.perf_counter() - started
    vectors, decode, run = _embed_photos(model, job.photos)
    readable = np.asarray([vector is not None for vector in vectors], dtype=np.bool_)
    width = next((len(vector) for vector in vectors if vector is not None), 1)
    images = np.stack(
        [np.zeros(width, np.float32) if v is None else v for v in vectors]
    )
    started = time.perf_counter()
    texts = (
        np.stack([model.text(query) for query in job.queries])
        if model.reads_text and job.queries
        else None
    )
    text_seconds = (time.perf_counter() - started) / max(1, len(job.queries))
    photos = max(1, int(readable.sum()))
    timing = Timing(
        load_seconds=load_seconds,
        decode_seconds=decode / photos,
        model_seconds=run / photos,
        text_seconds=text_seconds,
        peak_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / _KILOBYTES_PER_MB,
        model_mb=size_mb(SPECS[job.model], job.models_dir)
        if job.model in SPECS
        else 0.0,
        threads=job.threads,
        failed=len(job.photos) - int(readable.sum()),
    )
    return ModelRun(job.model, images, readable, texts, timing)


def _embed_photos(
    model: Embedder, photos: Sequence[Path]
) -> tuple[list[NDArray[np.float32] | None], float, float]:
    """Embed the photos one by one.

    Args:
        model: The model.
        photos: The photos.

    Returns:
        A vector per photo (None when it cannot be read), the seconds spent decoding,
        and those spent in the model.
    """
    vectors: list[NDArray[np.float32] | None] = []
    decode = run = 0.0
    for path in photos:
        started = time.perf_counter()
        try:
            picture = open_upright(path)
        except (
            OSError,
            UnidentifiedImageError,
            ValueError,
            Image.DecompressionBombError,
        ):
            vectors.append(None)
            continue
        decoded = time.perf_counter()
        vectors.append(model.image(picture))
        decode += decoded - started
        run += time.perf_counter() - decoded
    return vectors, decode, run
