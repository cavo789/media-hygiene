"""Photos given a place by hand (TODO 0237): found by content, never by path.

The GPS of the photos taken at grandpa's says "elsewhere in the village": these photos
only are given to the place, by their size then their SHA-256. A photo moved and
renamed since is still found; one edited since (new content) is not; another file of
the same size is not either; a file of another size is never read.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.hand_placed import Candidate, hand_placed, placed_by_hand
from media_hygiene.classify.models import SortReason
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.config.place_photos import HandPhoto, PlacePhotos
from media_hygiene.geo.gazetteer import Gazetteer
from tests.support.located import (
    GRANDPA,
    HOME,
    MILAN,
    PLACE_RULE,
    TRIP_RULE,
    located,
    start_of,
)
from tests.support.towns import write_towns

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput

CONTENT = b"the photo taken at grandpa's"
WRONG_GPS = (50.31, 5.1)  # elsewhere: neither home nor grandpa's


def _sha(data: bytes) -> str:
    """The SHA-256 of some bytes, as `full_digest` writes it."""
    return hashlib.sha256(data).hexdigest()


def _given(data: bytes = CONTENT, place: str = GRANDPA.name) -> PlacePhotos:
    """One photo of this content given to a place."""
    photo = HandPhoto(sha256=_sha(data), size=len(data), path="C:\\Photos\\IMG_1.jpg")
    return PlacePhotos(place=place, photos=(photo,))


def _write(folder: Path, name: str, data: bytes) -> Path:
    """A file of the given content."""
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def test_a_photo_moved_and_renamed_is_still_found(tmp_path: Path) -> None:
    """Its content names it: `sort`, `undo`, Explorer change nothing."""
    moved = _write(tmp_path, "2019/Geer/renamed.jpg", CONTENT)
    found = hand_placed([Candidate(moved, len(CONTENT))], [_given()])
    assert found == {moved: GRANDPA.name}


def test_a_photo_edited_since_is_not_found(tmp_path: Path) -> None:
    """New content, same size: it falls back to its GPS."""
    edited = _write(tmp_path, "IMG_1.jpg", CONTENT.upper())
    assert not hand_placed([Candidate(edited, len(CONTENT))], [_given()])


def test_only_the_files_of_a_listed_size_are_read(tmp_path: Path) -> None:
    """A file of another size is never hashed; one of the same size is, and differs."""
    other = _write(tmp_path, "other.jpg", b"x" * len(CONTENT))
    larger = _write(tmp_path, "larger.jpg", CONTENT + b"!")
    read: list[Path] = []

    def digest(candidate: Candidate) -> str | None:
        read.append(candidate.path)
        return _sha(candidate.path.read_bytes())

    candidates = [Candidate(other, len(CONTENT)), Candidate(larger, len(CONTENT) + 1)]
    assert not hand_placed(candidates, [_given()], digest)
    assert read == [other]


def test_the_index_digest_spares_reading_the_file(tmp_path: Path) -> None:
    """A digest the audit computed is used as is; a file gone is no error."""
    gone = tmp_path / "gone.jpg"
    known = Candidate(gone, len(CONTENT), _sha(CONTENT))
    unknown = Candidate(tmp_path / "unknown.jpg", len(CONTENT))
    assert hand_placed([known, unknown], [_given()]) == {gone: GRANDPA.name}


def _photo(where: tuple[float, float], name: str = "a.jpg") -> MediaInput:
    """A photo of the run whose content is `CONTENT` (its digest known)."""
    return replace(
        located(name, start_of(1), where), size=len(CONTENT), digest=_sha(CONTENT)
    )


def test_classify_puts_a_photo_given_by_hand_in_its_place() -> None:
    """Sure, as a GPS inside the place would be: its own GPS is ignored."""
    settings = ClassifySettings(
        rules=(PLACE_RULE,), places=(HOME, GRANDPA), place_photos=(_given(),)
    )
    [proposal] = classify([_photo(WRONG_GPS)], settings, Scope()).proposals
    assert (proposal.reason, proposal.folder) == (
        SortReason.PLACE,
        "2023/At grandpa's",
    )
    assert placed_by_hand([_photo(WRONG_GPS)], settings) == {
        _photo(WRONG_GPS).path: GRANDPA
    }


def test_a_trip_is_measured_from_the_place_given(tmp_path: Path) -> None:
    """A photo whose GPS says Milan, given to home, is no trip: it is home."""
    towns = Gazetteer.load(write_towns(tmp_path))
    settings = ClassifySettings(
        rules=(TRIP_RULE, PLACE_RULE),
        places=(HOME, GRANDPA),
        place_photos=(_given(place="home"),),  # any case
    )
    [proposal] = classify([_photo(MILAN)], settings, Scope(towns=towns)).proposals
    assert (proposal.reason, proposal.folder) == (SortReason.PLACE, "2023/Home")


def test_photos_given_to_no_place_are_refused() -> None:
    """Never an entry naming nothing: the map deletes them with their place."""
    with pytest.raises(ValidationError, match="Geer"):
        ClassifySettings(places=(HOME,), place_photos=(_given(place="Geer"),))
