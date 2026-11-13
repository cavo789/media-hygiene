"""Every photo version a model has read, at once (0815).

`FaceStore.scanned` and `TurnStore.guessed` ask one photo at a time: one query per
photo, twice, for a whole library (0.7 s at 100,000 photos, measured by 0794). A
plan reads each table once into a set and tests membership instead.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable, Sequence
    from pathlib import Path

    from media_hygiene.index.descriptions import PhotoVersion

type Version = tuple[str, int, int]

_SCANNED: Final = "SELECT path, size, mtime_ns FROM face_scans WHERE model = ?"
_GUESSED: Final = "SELECT path, size, mtime_ns FROM face_turns WHERE model = ?"


def version_of(photo: PhotoVersion) -> Version:
    """The key a photo's version is read under.

    Args:
        photo: The photo, with its size and mtime.

    Returns:
        Its path, size and mtime.
    """
    return (str(photo.path), photo.size, photo.mtime_ns)


def scanned_versions(connection: sqlite3.Connection, model: str) -> frozenset[Version]:
    """The photo versions whose faces (maybe none) the model found.

    Args:
        connection: The index.
        model: The face model.

    Returns:
        Their keys.
    """
    return frozenset(connection.execute(_SCANNED, (model,)))


def guessed_versions(connection: sqlite3.Connection, model: str) -> frozenset[Version]:
    """The photo versions whose turn (maybe none) the model guessed.

    Args:
        connection: The index.
        model: The face model.

    Returns:
        Their keys.
    """
    return frozenset(connection.execute(_GUESSED, (model,)))


def scanned_among(
    connection: sqlite3.Connection, model: str, photos: Iterable[PhotoVersion]
) -> int:
    """Count the photos whose faces the model found, in their current version.

    Args:
        connection: The index.
        model: The face model.
        photos: The photos, each once.

    Returns:
        How many were analysed.
    """
    found = scanned_versions(connection, model)
    return sum(version_of(photo) in found for photo in photos)


def unread(
    connection: sqlite3.Connection, model: str, photos: Sequence[PhotoVersion]
) -> tuple[set[Path], tuple[PhotoVersion, ...]]:
    """The photos the model analysed, and those it must read (again).

    Args:
        connection: The index.
        model: The face model.
        photos: The photos of the run, each once.

    Returns:
        The paths whose current version was scanned for faces; the photos not
        scanned, or whose turn is not guessed, in their order.
    """
    found = scanned_versions(connection, model)
    turned = guessed_versions(connection, model)
    scanned = {photo.path for photo in photos if version_of(photo) in found}
    missing = tuple(
        photo
        for photo in photos
        if photo.path not in scanned or version_of(photo) not in turned
    )
    return scanned, missing
