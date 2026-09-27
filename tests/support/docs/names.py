"""Where the demo library lies, and its folder names in each documented language."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


class Locale(StrEnum):
    """A language of the documentation (and of the tool)."""

    EN = "en"
    FR = "fr"


class Names(NamedTuple):
    """What the folders and files of the demo library are called."""

    old_disk: str
    holidays: str
    new_folder: str
    christmas: str
    hike: str
    birthday: str
    lake: str
    phone: str
    old_phone: str
    videos: str
    copy_suffix: str
    disk_photos: str
    disk_christmas: str
    email: str
    small: str
    video: str
    cut: str


NAMES: Final[Mapping[Locale, Names]] = {
    Locale.EN: Names(
        old_disk="Old disk",
        holidays="2019/Seaside holidays",
        new_folder="2019/New folder",
        christmas="2020/Christmas",
        hike="2021/Mountain hike",
        birthday="2022/Birthday",
        lake="2023/Lake",
        phone="Phone",
        old_phone="Old phone",
        videos="Videos",
        copy_suffix=" - Copy",
        disk_photos="Photos 2019",
        disk_christmas="Christmas 2020",
        email="Email",
        small=" small",
        video="Birthday.mp4",
        cut="Birthday (cut).mp4",
    ),
    Locale.FR: Names(
        old_disk="Ancien disque",
        holidays="2019/Vacances à la mer",
        new_folder="2019/Nouveau dossier",
        christmas="2020/Noël",
        hike="2021/Randonnée",
        birthday="2022/Anniversaire",
        lake="2023/Lac",
        phone="Téléphone",
        old_phone="Ancien téléphone",
        videos="Vidéos",
        copy_suffix=" - Copie",
        disk_photos="Photos 2019",
        disk_christmas="Noël 2020",
        email="Courriel",
        small=" petite",
        video="Anniversaire.mp4",
        cut="Anniversaire (coupée).mp4",
    ),
}


@dataclass(frozen=True, slots=True)
class Library:
    """Where the demo library is written, and in which language."""

    data: Path
    names: Names

    @property
    def photos(self) -> Path:
        r"""`C:\Photos`, as `/data/c/Photos`."""
        return self.data / "c" / "Photos"

    @property
    def disk(self) -> Path:
        r"""`D:\Old disk`, as `/data/d/Old disk`."""
        return self.data / "d" / self.names.old_disk
