"""Where the person page answers, under every page's server (TODO 0351)."""

from __future__ import annotations

from typing import Final

PERSON_PREFIX: Final = "/person"
PAGE_PATH: Final = PERSON_PREFIX
PHOTO_PATH: Final = f"{PERSON_PREFIX}/api/photo"
LOOK_PATH: Final = f"{PERSON_PREFIX}/api/look"
DRAW_PATH: Final = f"{PERSON_PREFIX}/api/draw"  # a face drawn by hand (0715)
FORGET_PATH: Final = f"{PERSON_PREFIX}/api/forget"  # one drawn by mistake, or twice
LIKE_PATH: Final = f"{PERSON_PREFIX}/api/like"
ASIDE_PATH: Final = f"{PERSON_PREFIX}/api/aside"
APPLY_PATH: Final = f"{PERSON_PREFIX}/api/apply"
UNDO_PATH: Final = f"{PERSON_PREFIX}/api/undo-run"
NAMES_PATH: Final = f"{PERSON_PREFIX}/api/names"  # name a face (0714)
ALBUMS_PATH: Final = f"{PERSON_PREFIX}/api/albums"  # and ▶ Slideshow (0657)
FACE_PREFIX: Final = f"{PERSON_PREFIX}/face/"
THUMB_PREFIX: Final = f"{PERSON_PREFIX}/thumb/"
PREVIEW_PREFIX: Final = f"{PERSON_PREFIX}/preview/"
JPEG: Final = ".jpg"


def is_person(path: str) -> bool:
    """Tell whether a request is the person page's.

    Args:
        path: The path asked for, its query included.

    Returns:
        True for `/person`, `/person?...` and below `/person/`.
    """
    return path.split("?", 1)[0] == PERSON_PREFIX or path.startswith(
        f"{PERSON_PREFIX}/"
    )
