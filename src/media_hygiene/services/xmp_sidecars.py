"""Where the sidecar of a photo lies: the one there, or the name of a new one."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.scan.sidecars import companions_of

if TYPE_CHECKING:
    from pathlib import Path

_XMP: Final = ".xmp"


def sidecar_of(photo: Path, folders: dict[Path, list[str]]) -> Path:
    """The sidecar of a photo: the one there, or the name of a new one.

    Args:
        photo: The photo.
        folders: The names of each folder listed so far (filled here).

    Returns:
        `IMG_1.jpg.xmp` (any case) when there; `IMG_1.xmp` when it belongs to this
        photo alone; else the name of a new `IMG_1.jpg.xmp`.
    """
    folder = photo.parent
    if folder not in folders:
        folders[folder] = sorted(entry.name for entry in folder.iterdir())
    names = folders[folder]
    whole = f"{photo.name}{_XMP}".casefold()
    stem = f"{photo.stem}{_XMP}".casefold()
    for name in names:
        if name.casefold() == whole:
            return folder / name
    for name in names:
        if name.casefold() == stem and companions_of(folder / name, names) == {
            photo.name
        }:
            return folder / name
    return folder / f"{photo.name}{_XMP}"
