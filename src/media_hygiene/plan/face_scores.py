"""Rank the shots of a burst by their faces, once `people` has looked at all of them.

A portrait burst may hold a frame with a sharp background and a blurred face. When
every shot of a series was looked at by `people` (a scan row of its current version, the
faces found or not) and at least half of them hold a face, the series is ranked by the
sharpness of its main faces, then by the frame's. A shot without a face comes after
those with faces. Any other series keeps the frame's sharpness. The faces come from the
index; the face models never run here.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import islice
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.plan.similar_models import BurstSeries, SimilarFindings
    from media_hygiene.scan.models import MediaFile, VisualFacts

# The pair of models of `faces.models.FACE_MODEL`, not imported: it loads numpy.
FACE_MODEL: Final = "yunet-2023mar+sface-2021dec"
# A main face is at least this share of the largest face of the shot (its area): an
# internal heuristic, not a setting. Every main face must be sharp.
MAIN_FACE_SHARE: Final = 0.5
_CHUNK: Final = 400
_FACES: Final = (
    "SELECT s.path, s.size, s.mtime_ns, f.width, f.height, f.sharpness"
    " FROM face_scans s LEFT JOIN faces f ON f.path = s.path AND f.model = s.model"
    " AND f.size = s.size AND f.mtime_ns = s.mtime_ns"
    " WHERE s.model = ? AND s.path IN ({marks})"
)


@dataclass(frozen=True, slots=True)
class Face:
    """The size and sharpness of one face."""

    area: float
    sharpness: float


def main_sharpness(faces: Sequence[Face]) -> float | None:
    """Give the sharpness of the least sharp main face of a shot.

    Args:
        faces: Its faces.

    Returns:
        The sharpness, or None for a shot without a face.
    """
    if not faces:
        return None
    largest = max(face.area for face in faces)
    return min(f.sharpness for f in faces if f.area >= largest * MAIN_FACE_SHARE)


def _add(found: dict[Path, list[Face]], file: MediaFile, row: Sequence[float]) -> None:
    """Add a face row to its shot, if it is of the file's current version."""
    size, mtime_ns, width, height, sharp = row
    if (file.size, file.mtime_ns) != (size, mtime_ns):
        return
    faces = found.setdefault(file.path, [])
    if width is not None:
        faces.append(Face(width * height, sharp))


def face_sharpness(
    connection: sqlite3.Connection, files: Iterable[MediaFile], model: str = FACE_MODEL
) -> Mapping[Path, float | None]:
    """Read, in the index, the main faces' sharpness of the shots looked at.

    Args:
        connection: The index.
        files: The shots, as audited.
        model: The pair of face models.

    Returns:
        Per shot looked at in its current version: the sharpness of its main faces, or
        None when no face was found. A shot never looked at is absent.
    """
    wanted = {str(file.path): file for file in files}
    found: dict[Path, list[Face]] = {}
    paths = iter(wanted)
    while chunk := list(islice(paths, _CHUNK)):
        query = _FACES.format(marks=",".join("?" * len(chunk)))
        for row in connection.execute(query, (model, *chunk)):
            _add(found, wanted[row[0]], row[1:])
    return MappingProxyType(
        {path: main_sharpness(faces) for path, faces in found.items()}
    )


def sharpness_order(faces: float | None, frame: float) -> tuple[bool, float, float]:
    """Make the sort key of a shot of a series ranked by its faces.

    Args:
        faces: Its main faces' sharpness, None without a face.
        frame: Its frame's sharpness.

    Returns:
        The key: faces first, sharper faces, sharper frame.
    """
    return (faces is not None, faces or 0.0, frame)


def faced(
    series: BurstSeries, scores: Mapping[Path, float | None]
) -> Mapping[Path, float | None]:
    """Tell whether a series is ranked by its faces, and give its shots' scores.

    Args:
        series: The series.
        scores: What `face_sharpness` read.

    Returns:
        The scores of its shots, empty when a shot was not looked at or fewer than
        half of the shots hold a face.
    """
    own = {file.path: scores[file.path] for file in series.shots if file.path in scores}
    looked = sum(score is not None for score in own.values())
    if len(own) < len(series.shots) or 2 * looked < len(series.shots):
        return {}
    return own


def starred_by_faces(
    similar: SimilarFindings, scores: Mapping[Path, float | None]
) -> SimilarFindings:
    """Put the ⭐ of the series looked at on the shot whose faces are sharpest.

    Args:
        similar: The findings of the audit.
        scores: What `face_sharpness` read.

    Returns:
        The findings, the series ranked by faces re-ranked, their scores in `faced`.
    """
    bursts: list[BurstSeries] = []
    ranked: dict[Path, float | None] = {}
    for series in similar.bursts:
        own = faced(series, scores)
        ranked.update(own)
        bursts.append(_starred(series, own, similar.visuals) if own else series)
    return replace(similar, bursts=tuple(bursts), faced=MappingProxyType(ranked))


def _starred(
    series: BurstSeries,
    own: Mapping[Path, float | None],
    visuals: Mapping[Path, VisualFacts],
) -> BurstSeries:
    """Give the series the ⭐ of the shot whose faces are sharpest."""

    def key(file: MediaFile) -> tuple[bool, float, float]:
        """Faces first, then the frame.

        Args:
            file: A shot of the series.

        Returns:
            The sort key.
        """
        return sharpness_order(own[file.path], visuals[file.path].sharpness)

    return replace(series, best=max(series.shots, key=key))


def rank_by_faces(
    similar: SimilarFindings, connection: sqlite3.Connection
) -> SimilarFindings:
    """Read the faces of the burst shots in the index (one query) and rank by them.

    Args:
        similar: The findings of the audit.
        connection: The index.

    Returns:
        The findings, the series looked at by `people` ranked by their faces.
    """
    shots = [file for series in similar.bursts for file in series.shots]
    return (
        starred_by_faces(similar, face_sharpness(connection, shots))
        if shots
        else similar
    )
