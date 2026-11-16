"""The photos given a place by hand, found where they were listed first (2026-11-16).

`hand_placed` finds them by content id: size, then SHA-256, read from the disk when
the index keeps no digest, as for most photos (a digest is kept for the files that
share their size). The library read every listed photo again at each list of its
places: 3.9 s for three places on the maintainer's PC (measured, slow log). A photo
still at the path it was listed with, with the same size, is that photo, as the
index trusts a path and its size; the digest is read for the others only (moved,
renamed, or a copy elsewhere).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.classify.hand_placed import Candidate, digest_of, hand_placed
from media_hygiene.config.face_refs import container_of, face_mapper
from media_hygiene.config.photo_ref import size_of
from media_hygiene.review.slow_log import Laps

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from media_hygiene.config.place_photos import PlacePhotos


def placed_where(
    rows: Iterable[tuple[str, int, str | None]], given: Sequence[PlacePhotos]
) -> dict[Path, str]:
    """The files given a place by hand, and the place's name as written.

    Args:
        rows: Each file of the index: its path, size and digest (None: not kept).
        given: `[[classify.place_photos]]`.

    Returns:
        The place of each file found.
    """
    mapper = face_mapper()
    listed = {
        container_of(photo.path, mapper): (size_of(photo.id), entry.place)
        for entry in given
        for photo in entry.photos
        if photo.path
    }
    found: dict[Path, str] = {}
    others: list[Candidate] = []
    for text, size, digest in rows:
        path = Path(text)
        here = listed.get(path)
        if here is not None and here[0] == size:
            found[path] = here[1]
        else:
            others.append(Candidate(path, size, digest))
    read: list[Path] = []

    def counted(candidate: Candidate) -> str | None:
        """A candidate's digest, counted for the slow line.

        Args:
            candidate: The file.

        Returns:
            Its SHA-256, as `digest_of` gives it.
        """
        read.append(candidate.path)
        return digest_of(candidate)

    laps = Laps(f"{len(listed)} listed by hand, {len(found)} at their path")
    placed = hand_placed(others, given, counted)
    laps.lap(f"{len(read)} digests, {sum(1 for c in others if c.digest)} kept")
    laps.said()
    return {**placed, **found}
