"""A burst's star follows the sharpness of its faces once `people` has looked at all."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import MediaKind
from media_hygiene.faces import models
from media_hygiene.faces.models import Face, FaceBox, PhotoFaces
from media_hygiene.index.face_rows import FaceStore
from media_hygiene.index.repository import FactsRepository
from media_hygiene.plan.burst_proposals import (
    AsideReason,
    Proposal,
    ProposalLimits,
    ShotLook,
    propose,
)
from media_hygiene.plan.face_scores import (
    FACE_MODEL,
    face_sharpness,
    main_sharpness,
    rank_by_faces,
)
from media_hygiene.plan.face_scores import (
    Face as Measured,
)
from media_hygiene.plan.similar_models import BurstSeries, SimilarFindings
from media_hygiene.review.shares import shares
from media_hygiene.scan.models import MediaFile, VisualFacts

if TYPE_CHECKING:
    import sqlite3

MODEL: Final = FACE_MODEL
assert MODEL == models.FACE_MODEL
DATA: Final = Path("/data/c")


def shot(name: str) -> MediaFile:
    """An image below /data/c, 10 bytes, mtime 1."""
    return MediaFile(DATA / name, 10, 1, MediaKind.IMAGE)


def face(side: float, sharpness: float) -> Face:
    """A square face of this side and sharpness."""
    return Face(FaceBox(0, 0, side, side), (0.0,) * 10, 0.9, sharpness, b"")


def look(sharpness: float) -> VisualFacts:
    """Visual facts with only the frame's sharpness mattering."""
    return VisualFacts(dhash=0, phash=0, width=4, height=3, sharpness=sharpness)


def scan(
    connection: sqlite3.Connection, file: MediaFile, *faces: Face, mtime_ns: int = 1
) -> None:
    """Record that `people` looked at a shot, with these faces."""
    FaceStore(connection, MODEL).put(
        PhotoFaces(file.path, file.size, mtime_ns, tuple(faces), 0.1)
    )


def findings(files: list[MediaFile], frames: list[float]) -> SimilarFindings:
    """One burst series whose ⭐ is the sharpest frame."""
    visuals = {
        file.path: look(frame) for file, frame in zip(files, frames, strict=True)
    }
    best = max(files, key=lambda file: visuals[file.path].sharpness)
    return SimilarFindings(bursts=(BurstSeries(tuple(files), best),), visuals=visuals)


def best_of(similar: SimilarFindings) -> str:
    """The name of the ⭐ of the only series."""
    return similar.bursts[0].best.path.name


def test_a_shot_with_a_blurred_main_face_loses_the_star() -> None:
    """The sharpest frame has a blurred face among two: the sharp faces win."""
    files = [shot("a.jpg"), shot("b.jpg"), shot("c.jpg")]
    similar = findings(files, [900.0, 500.0, 400.0])
    with FactsRepository.open(None) as repository:
        db = repository.connection
        scan(db, files[0], face(100, 400), face(90, 5))  # frame sharp, one face blurred
        scan(db, files[1], face(100, 300), face(90, 280))
        scan(db, files[2], face(100, 200))
        ranked = rank_by_faces(similar, db)
    assert best_of(similar) == "a.jpg"
    assert best_of(ranked) == "b.jpg"
    assert ranked.faced[files[0].path] == 5


def test_small_faces_do_not_count_as_main_faces() -> None:
    """A face under half the area of the largest is background, not a main face."""
    assert main_sharpness([]) is None
    faces = [face(100, 300), face(50, 1)]  # 25 % of the area
    assert main_sharpness([Measured(f.box.width**2, f.sharpness) for f in faces]) == 300


def test_a_series_not_fully_looked_at_keeps_the_frame_order() -> None:
    """One shot never looked at, or looked at in an older version: as today."""
    files = [shot("a.jpg"), shot("b.jpg"), shot("c.jpg")]
    similar = findings(files, [900.0, 500.0, 400.0])
    with FactsRepository.open(None) as repository:
        db = repository.connection
        scan(db, files[0], face(100, 1))
        scan(db, files[1], face(100, 300))
        scan(db, files[2], face(100, 300), mtime_ns=2)  # the file changed since
        ranked = rank_by_faces(similar, db)
    assert best_of(ranked) == "a.jpg"
    assert not ranked.faced


def test_a_series_with_few_faces_keeps_the_frame_order() -> None:
    """Looked at, but fewer than half of the shots hold a face: as today."""
    files = [shot("a.jpg"), shot("b.jpg"), shot("c.jpg")]
    similar = findings(files, [900.0, 500.0, 400.0])
    with FactsRepository.open(None) as repository:
        db = repository.connection
        scan(db, files[0])
        scan(db, files[1], face(100, 300))
        scan(db, files[2])
        assert not rank_by_faces(similar, db).faced


def test_a_shot_without_a_face_comes_after_those_with_faces() -> None:
    """Even with the sharpest frame; the faces are read once, by one query."""
    files = [shot("a.jpg"), shot("b.jpg"), shot("c.jpg")]
    similar = findings(files, [900.0, 100.0, 90.0])
    with FactsRepository.open(None) as repository:
        db = repository.connection
        scan(db, files[0])
        scan(db, files[1], face(100, 10))
        scan(db, files[2], face(100, 20))
        scores = face_sharpness(db, files)
        ranked = rank_by_faces(similar, db)
    assert scores == {files[0].path: None, files[1].path: 10, files[2].path: 20}
    assert best_of(ranked) == "c.jpg"
    assert ranked.faced[files[0].path] is None


def test_the_proposals_and_their_shares_follow_the_faces() -> None:
    """A shot whose faces are far less sharp is proposed aside, for its faces."""
    limits = ProposalLimits(sharpness_below=0.5)
    best = ShotLook(100.0, 0, keep=True, faced=True, faces=400.0)
    blurred = ShotLook(900.0, 1 << 40, faced=True, faces=40.0)
    plain = ShotLook(900.0, 1 << 50, faced=True, faces=300.0)
    faceless = ShotLook(10.0, 1 << 60, faced=True, faces=None)
    proposals = propose((best, blurred, plain, faceless), limits)
    assert proposals == {
        1: Proposal(AsideReason.FACES),
        3: Proposal(AsideReason.BLURRIER),
    }
    assert shares((best, blurred, plain, faceless)) == (1.0, 0.1, 0.75, 1.0)
    assert shares((replace(best, faced=False, faces=None), None)) == (1.0, None)
