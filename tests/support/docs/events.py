"""The events of the demo library: a hike, a birthday, a lake, a phone, a video."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Final

from tests.support.docs.pictures import Kind, Picture
from tests.support.docs.shots import PHONE, Shot, copy, truncate, video, write_shot

if TYPE_CHECKING:
    from tests.support.docs.names import Library

LATER: Final = datetime(2024, 1, 15, 20, 30, tzinfo=UTC)  # when the copies were made


def hike(library: Library) -> None:
    """Ten hike photos, three of them a burst: one second apart, the camera panning."""
    folder, start = (
        library.photos / library.names.hike,
        datetime(2021, 8, 14, 9, tzinfo=UTC),
    )
    for index in range(1, 11):
        kind = Kind.MOUNTAINS if index % 3 else Kind.MEADOW
        picture, when = Picture(kind, 20 + index), start + timedelta(minutes=23 * index)
        if index in {6, 7, 8}:
            picture = Picture(Kind.MOUNTAINS, 60, pan=20 + 12 * (index - 6))
            when = start + timedelta(minutes=23 * 6, seconds=index - 6)
        write_shot(folder / f"DSC_{2100 + index:04d}.jpg", Shot(picture, when))


def birthday(library: Library) -> None:
    """A burst of five birthday shots, the third one shaken, then three other photos."""
    folder, party = (
        library.photos / library.names.birthday,
        datetime(2022, 5, 21, 16, 30, tzinfo=UTC),
    )
    for shot in range(5):
        picture = Picture(Kind.BALLOONS, 1, pan=10 + 10 * shot, shaken=shot == 2)
        write_shot(
            folder / f"IMG_{3001 + shot:04d}.jpg",
            Shot(picture, party + timedelta(seconds=shot)),
        )
    for index in range(3):
        when = party + timedelta(minutes=20 * (index + 1))
        write_shot(
            folder / f"IMG_{3010 + index:04d}.jpg",
            Shot(Picture(Kind.BALLOONS, 10 + index), when),
        )


def lake(library: Library) -> None:
    """A burst of four sunset shots over a lake, then two meadow photos."""
    folder, evening = (
        library.photos / library.names.lake,
        datetime(2023, 9, 2, 20, 5, tzinfo=UTC),
    )
    for shot in range(4):
        picture = Picture(Kind.SUNSET, 40, pan=15 + 14 * shot)
        write_shot(
            folder / f"IMG_{4001 + shot:04d}.jpg",
            Shot(picture, evening + timedelta(seconds=2 * shot)),
        )
    for index in range(2):
        when = evening + timedelta(hours=index + 1)
        write_shot(
            folder / f"IMG_{4010 + index:04d}.jpg",
            Shot(Picture(Kind.MEADOW, 40 + index), when),
        )


def phone(library: Library) -> None:
    """Three iPhone photos (HEIC), all copied on the old disk."""
    kinds = (Kind.MEADOW, Kind.BEACH, Kind.MOUNTAINS)
    for index, kind in enumerate(kinds):
        when = datetime(2024, 4, 6, 11, tzinfo=UTC) + timedelta(minutes=41 * index)
        name = f"IMG_{4242 + index}.HEIC"
        heic = write_shot(
            library.photos / library.names.phone / name,
            Shot(Picture(kind, 70 + index), when, PHONE),
        )
        copy(
            heic, library.disk / library.names.phone / name, LATER + timedelta(days=200)
        )


def videos(library: Library) -> None:
    """A birthday video, copied on the old disk, where a second copy was cut short."""
    names = library.names
    party = datetime(2022, 5, 21, 16, 35, tzinfo=UTC)
    original = video(library.photos / names.videos / names.video, party)
    copy(original, library.disk / names.videos / names.video, LATER)
    truncate(original, library.disk / names.videos / names.cut)
