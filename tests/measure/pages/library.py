"""A synthetic index shaped like a real library, written by the index's own writers.

No picture is written: the rows say what an audit and `tags` would have found. The
shape follows the maintainer's measured library (2026-10-17, 52,094 media): 2.9 %
videos, 9 % undated, 1.3 % with GPS, about 0.52 face per file; folders
`<year>/<event>/` of about 40 files.
"""

from __future__ import annotations

import os
import random
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.constants import MediaKind
from media_hygiene.faces.models import (
    EMBEDDING_SIZE,
    FACE_MODEL,
    Face,
    FaceBox,
    PhotoFaces,
)
from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.face_rows import FaceStore
from media_hygiene.index.facts import FileFacts
from media_hygiene.index.rows import row_of
from media_hygiene.index.schema import UPSERT, prepare
from media_hygiene.index.tag_rows import TagStore
from media_hygiene.scan.metadata import METADATA_VERSION, MediaMetadata
from media_hygiene.scan.models import MediaFile, VisualFacts
from media_hygiene.tags.models import FileTags, PlaceKind, Tag, TagSource

if TYPE_CHECKING:
    from pathlib import Path

SIZES: Final = (10_000, 100_000, 300_000)
FILES_PER_FOLDER: Final = 40
VIDEO_SHARE: Final = 0.029
UNDATED_SHARE: Final = 0.09
GPS_SHARE: Final = 0.013
FACES_PER_FILE: Final = 0.52
PEOPLE: Final = 60  # distinct faces the embeddings gather around
UNSORTED_TENTHS: Final = 2  # of the folders: a camera's dump, not sorted yet
FIRST_YEAR: Final = 2000
YEARS: Final = 26
_EVENTS: Final = (
    "Vacances", "Noel", "Anniversaire", "Mariage", "Plage", "Montagne", "Ski",
    "Durbuy", "Paris", "Rome", "Barcelone", "Bapteme", "Pique-nique", "Jardin",
)  # fmt: skip
# Towns and where they lie: the GPS photos are around them.
_TOWNS: Final = (
    ("Durbuy", 50.35, 5.46),
    ("Paris", 48.86, 2.35),
    ("Rome", 41.90, 12.50),
    ("Barcelona", 41.39, 2.17),
    ("Chamonix", 45.92, 6.87),
)
_BATCH: Final = 5_000
_SPREAD: Final = 0.02  # degrees around a town
_NOISE: Final = 0.35  # of a face vector around its person


@dataclass(frozen=True, slots=True)
class Library:
    """Where the synthetic index goes and how many files it lists."""

    index: Path
    data: Path  # the mounted folder the paths lie under (`/data/c`)
    count: int


def _file(library: Library, number: int) -> tuple[MediaFile, int, str]:
    """The file of a number, its year and its event folder.

    Args:
        library: The library.
        number: From 0.

    Returns:
        The file, its year, its event.
    """
    folder = number // FILES_PER_FOLDER
    year = FIRST_YEAR + folder % YEARS
    event = _EVENTS[folder % len(_EVENTS)]
    video = random.random() < VIDEO_SHARE  # noqa: S311 - synthetic data
    name = f"VID_{number:06d}.mp4" if video else f"IMG_{number:06d}.jpg"
    month = f"{year}-{folder % 12 + 1:02d}"
    if folder % 10 < UNSORTED_TENTHS:  # a camera's dump, not sorted yet
        path = library.data / "Photos" / "A trier" / f"DCIM {folder}" / name
    else:
        path = library.data / "Photos" / str(year) / month / f"{event} {folder}" / name
    kind = MediaKind.VIDEO if video else MediaKind.IMAGE
    size = random.randint(2_000_000, 6_000_000)  # noqa: S311
    return MediaFile(path, size, 1_700_000_000_000_000_000 + number, kind), year, event


def _facts(year: int, number: int) -> FileFacts:
    """What an audit found: a date (or none), a camera, GPS for a few.

    Args:
        year: The folder's year.
        number: The file's number.

    Returns:
        The facts.
    """
    undated = random.random() < UNDATED_SHARE  # noqa: S311
    folder = number // FILES_PER_FOLDER
    day = f"{year}-{folder % 12 + 1:02d}-{folder % 28 + 1:02d}"
    taken = None if undated else f"{day}T{number % 24:02d}:00:00"
    town = _TOWNS[number % len(_TOWNS)]
    located = random.random() < GPS_SHARE  # noqa: S311
    metadata = MediaMetadata(
        latitude=town[1] + random.uniform(-_SPREAD, _SPREAD) if located else None,  # noqa: S311
        longitude=town[2] + random.uniform(-_SPREAD, _SPREAD) if located else None,  # noqa: S311
        make="Canon",
        model="EOS 80D",
        file_format="JPEG",
    )
    visual = VisualFacts(
        dhash=random.getrandbits(64),
        phash=random.getrandbits(64),
        width=4000,
        height=3000,
        sharpness=random.uniform(10, 900),  # noqa: S311
        taken_at=taken,
        camera="Canon EOS 80D",
    )
    digest = f"{number:064x}"
    return FileFacts(
        partial_digest=digest,
        full_digest=digest,
        integrity=None,
        visual_checked=True,
        visual=visual,
        metadata_version=METADATA_VERSION,
        metadata=metadata,
    ).with_integrity(None, "")


def _tags(file: MediaFile, year: int, event: str) -> FileTags:
    """The tags `tags` would give: folder words, the year, a town for some events.

    Args:
        file: The file.
        year: Its year.
        event: Its event folder's word.

    Returns:
        Its tags.
    """
    words = [Tag(TagSource.FOLDER, event.lower()), Tag(TagSource.DATE, str(year))]
    town = next((name for name, _, _ in _TOWNS if name.startswith(event[:4])), None)
    if town is not None:
        words.append(Tag(TagSource.PLACE, town.lower(), kinds=(PlaceKind.TOWN,)))
    return FileTags(PhotoVersion(file.path, file.size, file.mtime_ns), tuple(words))


def _faces(file: MediaFile, people: np.ndarray, count: int) -> PhotoFaces:
    """Faces of some people, their vectors near those people's.

    Args:
        file: The photo.
        people: One unit vector per person.
        count: How many faces.

    Returns:
        The photo's faces.
    """
    found = []
    for _ in range(count):
        vector = people[random.randrange(len(people))]  # noqa: S311
        noisy = vector + np.random.default_rng().normal(0, _NOISE / 10, EMBEDDING_SIZE)
        unit = (noisy / np.linalg.norm(noisy)).astype(np.float32)
        box = FaceBox(100.0, 100.0, 200.0, 240.0)
        found.append(Face(box, (0.0,) * 10, 0.95, 120.0, unit.tobytes()))
    return PhotoFaces(file.path, file.size, file.mtime_ns, tuple(found), 0.1)


def _placeholder(file: MediaFile) -> None:
    """An empty sparse file of the file's size and mtime: `people` checks it is there.

    Args:
        file: The file listed.
    """
    file.path.parent.mkdir(parents=True, exist_ok=True)
    with file.path.open("wb") as handle:
        handle.truncate(file.size)
    os.utime(file.path, ns=(file.mtime_ns, file.mtime_ns))


def build(library: Library) -> None:
    """Write the index (files, tags, faces, in batches) and a placeholder per file.

    Args:
        library: Where, and how many files.
    """
    random.seed(678)
    generator = np.random.default_rng(678)
    people = generator.normal(size=(PEOPLE, EMBEDDING_SIZE))
    people /= np.linalg.norm(people, axis=1, keepdims=True)
    library.index.unlink(missing_ok=True)
    with closing(sqlite3.connect(library.index)) as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = OFF")
        prepare(connection)
        tags, faces = TagStore(connection), FaceStore(connection, FACE_MODEL)
        for start in range(0, library.count, _BATCH):
            numbers = range(start, min(start + _BATCH, library.count))
            files = [_file(library, number) for number in numbers]
            connection.executemany(
                UPSERT,
                [
                    row_of(file, _facts(year, n))
                    for n, (file, year, _) in zip(numbers, files, strict=True)
                ],
            )
            sources = (TagSource.FOLDER, TagSource.DATE, TagSource.PLACE)
            tags.replace(
                sources, [_tags(file, year, event) for file, year, event in files]
            )
            for file, _, _ in files:
                _placeholder(file)
                if file.kind is MediaKind.IMAGE:
                    count = np.random.default_rng().poisson(FACES_PER_FILE)
                    faces.put(_faces(file, people, int(count)))
        connection.commit()
