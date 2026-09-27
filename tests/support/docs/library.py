r"""The demo library: C:\Photos, a family library, and D:\Old disk, full of copies.

Exact copies (across disks, inside a folder, with copy names), three burst series
(one shot shaken), two near duplicates (WhatsApp, e-mail), broken files and sidecars
(one left orphan).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Final

from tests.support.docs.events import LATER, birthday, hike, lake, phone, videos
from tests.support.docs.names import NAMES, Library
from tests.support.docs.pictures import Kind, Picture
from tests.support.docs.shots import Shot, copy, truncate, write_shot

if TYPE_CHECKING:
    from pathlib import Path

    from tests.support.docs.names import Locale
_HOLIDAYS: Final = (Kind.BEACH,) * 5 + (Kind.SUNSET,) * 4 + (Kind.MEADOW,) * 3
_XMP: Final = "<x:xmpmeta/>\n"


def _holidays(library: Library) -> list[Path]:
    """Twelve holiday photos, two with a sidecar, copied everywhere."""
    folder, names = library.photos / library.names.holidays, library.names
    photos = []
    for index, kind in enumerate(_HOLIDAYS, start=1):
        when = datetime(2019, 7, 10, 10, tzinfo=UTC) + timedelta(
            hours=7 * index, minutes=13 * index
        )
        photos.append(
            write_shot(
                folder / f"IMG_{100 + index:04d}.jpg", Shot(Picture(kind, index), when)
            )
        )
    for number in (102, 103):
        (folder / f"IMG_{number:04d}.xmp").write_text(_XMP, encoding="utf-8")
    copy(photos[0], folder / "IMG_0101 (1).jpg", LATER)
    for index in (5, 6, 7):
        name = f"IMG_{100 + index:04d}{names.copy_suffix}.jpg"
        copy(photos[index - 1], library.photos / names.new_folder / name, LATER)
    for index, photo in enumerate(photos[:8], start=1):
        copy(
            photo,
            library.photos / names.old_phone / f"IMG_{100 + index:04d}.jpg",
            LATER + timedelta(days=30),
        )
    for index, photo in enumerate(photos, start=1):
        copy(
            photo,
            library.disk / names.disk_photos / f"IMG_{100 + index:04d}.jpg",
            LATER + timedelta(days=60),
        )
    # Both copies of IMG_0102 have a sidecar: the deleted copy's one is left orphan.
    (library.disk / names.disk_photos / "IMG_0102.xmp").write_text(
        _XMP, encoding="utf-8"
    )
    return photos


def _near_duplicates(library: Library) -> None:
    """Two holiday photos saved again, undated: smaller (WhatsApp), recompressed."""
    whatsapp = Shot(Picture(Kind.BEACH, 4), None, None, 70, (800, 533))
    write_shot(library.photos / "WhatsApp" / "IMG-20190712-WA0003.jpg", whatsapp)
    email = Shot(Picture(Kind.MEADOW, 10), None, None, 45, (1024, 683))
    name = f"IMG_0110{library.names.small}.jpg"
    write_shot(library.disk / library.names.email / name, email)


def _christmas(library: Library) -> None:
    """Six Christmas photos, four copied on the old disk, one of them broken there."""
    folder, names = library.photos / library.names.christmas, library.names
    photos = []
    for index in range(1, 7):
        when = datetime(2020, 12, 24, 17, tzinfo=UTC) + timedelta(
            hours=3 * index, minutes=7 * index
        )
        photos.append(
            write_shot(
                folder / f"IMG_{1200 + index:04d}.jpg",
                Shot(Picture(Kind.CHRISTMAS, index), when),
            )
        )
    for index, photo in enumerate(photos[:4], start=1):
        copy(
            photo,
            library.disk / names.disk_christmas / f"IMG_{1200 + index:04d}.jpg",
            LATER,
        )
    (library.disk / "2020").mkdir(parents=True, exist_ok=True)
    (library.disk / "2020" / "IMG_9999.jpg").touch()
    truncate(photos[2], library.disk / "2020" / "IMG_1203.jpg")


def build_library(locale: Locale, data: Path) -> Library:
    """Write the whole demo library.

    Args:
        locale: The language of its folder names.
        data: The folder standing for `/data`.

    Returns:
        Where it was written.
    """
    library = Library(data, NAMES[locale])
    _holidays(library)
    _near_duplicates(library)
    _christmas(library)
    hike(library)
    birthday(library)
    lake(library)
    phone(library)
    videos(library)
    return library
