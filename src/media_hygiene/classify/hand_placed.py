"""The photos given a place by hand, found by content: size, then SHA-256 (0237).

Only the files whose size equals a listed photo's are hashed, unless the index already
knows their digest: never the whole collection. A photo moved or renamed since is still
found; one edited since (new content) is not, and falls back to its GPS.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.scan.hashing import full_digest

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.config.classify_places import PersonalPlace
    from media_hygiene.config.classify_settings import ClassifySettings
    from media_hygiene.config.place_photos import PlacePhotos


@dataclass(frozen=True, slots=True)
class Candidate:
    """A file that may be a listed photo: its size, its digest when known."""

    path: Path
    size: int
    digest: str | None = None


def digest_of(candidate: Candidate) -> str | None:
    """A file's SHA-256: the index's, else read from the disk.

    Args:
        candidate: The file.

    Returns:
        The hex digest; None when the file cannot be read (moved, not mounted).
    """
    if candidate.digest:
        return candidate.digest
    try:
        return full_digest(candidate.path)
    except OSError:
        return None


def hand_placed(
    candidates: Iterable[Candidate],
    given: Sequence[PlacePhotos],
    digest: Callable[[Candidate], str | None] = digest_of,
) -> dict[Path, str]:
    """Find the files that are photos given a place.

    Args:
        candidates: The files, with their size.
        given: `[[classify.place_photos]]`.
        digest: How to get a file's SHA-256 (the map keeps the ones it read).

    Returns:
        The place's name (as written in the entry) of each file found.
    """
    by_size: defaultdict[int, dict[str, str]] = defaultdict(dict)
    for entry in given:
        for photo in entry.photos:
            by_size[photo.size][photo.sha256] = entry.place
    found: dict[Path, str] = {}
    for candidate in candidates:
        listed = by_size.get(candidate.size)
        if not listed:
            continue
        sha = digest(candidate)
        if sha is not None and sha in listed:
            found[candidate.path] = listed[sha]
    return found


def placed_by_hand(
    files: Sequence[MediaInput], settings: ClassifySettings
) -> Mapping[Path, PersonalPlace]:
    """The files of a run given a place by hand, and their place.

    Args:
        files: The files of the run.
        settings: `[classify]`: the places and the photos given them.

    Returns:
        The place of each file found.
    """
    if not settings.place_photos:
        return {}
    places = {place.name.casefold(): place for place in settings.places}
    candidates = (Candidate(file.path, file.size, file.digest) for file in files)
    return {
        path: places[name.casefold()]
        for path, name in hand_placed(candidates, settings.place_photos).items()
        if name.casefold() in places
    }
