"""The events of the demo library: a hike, a birthday, a lake, a phone, videos."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Final

from tests.support.docs.pictures import Kind, Picture
from tests.support.docs.shots import (
    PHONE,
    Shot,
    copy,
    reencode,
    truncate,
    video,
    write_shot,
)

if TYPE_CHECKING:
    from tests.support.docs.names import Library

# Public places, synthetic photos: a Brussels park, the lake of Genval.
PARK: Final = (
    50.841,
    4.393,
)  # middle of a 0.002 degree cell: stays one cluster
GENVAL: Final = (50.719, 4.489)
_JITTER: Final = 0.0002  # about 20 m a step: one cluster of the `places` map
LATER: Final = datetime(2024, 1, 15, 20, 30, tzinfo=UTC)  # when the copies were made


def near(place: tuple[float, float], step: int) -> tuple[float, float]:
    """A position a few metres from a place, a different one at each step."""
    return (place[0] + _JITTER * (step % 3 - 1), place[1] + _JITTER * (step % 4 - 1.5))


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
            picture = Picture(Kind.MOUNTAINS, 60, 20 + 12 * (index - 6), pose=index - 6)
            when = start + timedelta(minutes=23 * 6, seconds=index - 6)
        write_shot(folder / f"DSC_{2100 + index:04d}.jpg", Shot(picture, when))


def birthday(library: Library) -> None:
    """A burst of five birthday shots, the third one shaken, then three other photos."""
    folder, party = (
        library.photos / library.names.birthday,
        datetime(2022, 5, 21, 16, 30, tzinfo=UTC),
    )
    for shot in range(5):
        picture = Picture(Kind.BALLOONS, 1, 10 + 10 * shot, shot == 2, pose=shot)
        write_shot(
            folder / f"IMG_{3001 + shot:04d}.jpg",
            Shot(picture, party + timedelta(seconds=shot), gps=near(PARK, shot)),
        )
    for index in range(3):
        when = party + timedelta(minutes=20 * (index + 1))
        write_shot(
            folder / f"IMG_{3010 + index:04d}.jpg",
            Shot(Picture(Kind.BALLOONS, 10 + index), when, gps=near(PARK, index + 5)),
        )


def lake(library: Library) -> None:
    """A burst of four sunset shots over a lake, then two meadow photos.

    The four are positioned at Genval, yet the `places` map shows 3 photos: the
    burst review sets IMG_4002 aside, `clean --decisions` then `purge` remove it.
    """
    folder, evening = (
        library.photos / library.names.lake,
        datetime(2023, 9, 2, 20, 5, tzinfo=UTC),
    )
    for shot in range(4):
        picture = Picture(Kind.SUNSET, 40, 15 + 14 * shot, pose=shot)
        write_shot(
            folder / f"IMG_{4001 + shot:04d}.jpg",
            Shot(
                picture,
                evening + timedelta(seconds=2 * shot),
                gps=near(GENVAL, shot),
            ),
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
    """A birthday video, copied on the old disk (a copy cut short), sent by WhatsApp."""
    names = library.names
    party = datetime(2022, 5, 21, 16, 35, tzinfo=UTC)
    original = video(library.photos / names.videos / names.video, party)
    copy(original, library.disk / names.videos / names.video, LATER)
    truncate(original, library.disk / names.videos / names.cut)
    sent = library.photos / "WhatsApp" / "VID-20220521-WA0001.mp4"
    reencode(original, sent, party + timedelta(minutes=5))
