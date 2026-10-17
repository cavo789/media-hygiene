"""Google Photos Takeout: which photo or video each `.json` file describes.

A Takeout (takeout.google.com) gives one `.json` file per photo or video, next to it:
`IMG_1234.jpg.json` in older ones, `IMG_1234.jpg.supplemental-metadata.json` in newer
ones. Google truncates long names, the suffix included (`.supplemental-me.json`), and
the photo's own name with it; the number of a duplicate name moves to the end
(`IMG_1234(1).jpg` ↔ `IMG_1234.jpg(1).json`); `&` and `?` become `_`; an edited
version (`IMG_1234-edited.jpg`) shares its original's file. These rules come from the
tools that read Takeouts: no real Takeout was at hand to check them.

A `.json` that matches no media file of its folder is not a sidecar: it is left alone.
"""

from __future__ import annotations

import re
from pathlib import PurePath
from typing import TYPE_CHECKING, Final

from media_hygiene.scan.takeout_folder import (
    JSON_SUFFIX,
    folder_names,
    name_key,
    stem_of,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.scan.takeout_folder import FolderNames

_METADATA_WORD: Final = "supplemental-metadata"
_EDITED: Final = "-edited"
# Below this length, a JSON name was not truncated: its photo's name is whole.
TRUNCATED_FROM: Final = 46
_NUMBER: Final = re.compile(r"^(?P<name>.*?)(?P<number>\(\d+\))$")


def is_takeout_json(name: str) -> bool:
    """Tell whether a file name may be the `.json` of a Takeout.

    Args:
        name: A file name.

    Returns:
        True for a `.json` file (any case).
    """
    return name.casefold().endswith(JSON_SUFFIX)


def takeout_owners(json_name: str, names: Iterable[str]) -> frozenset[str]:
    """Return the names, among `names`, of the files a Takeout `.json` describes.

    The original, or its single match when the name was truncated, and its edited
    versions; an edited version alone when its original is gone.

    Args:
        json_name: The `.json` file's name.
        names: Names of the other files of its folder.

    Returns:
        Those names; empty when the `.json` is not a Takeout one, or ambiguous.
    """
    if not is_takeout_json(json_name):
        return frozenset()
    described = _numbered(*_described(json_name[: -len(JSON_SUFFIX)]))
    folder = folder_names(tuple(names))
    original = _original(described, folder, len(json_name))
    edited = f"{stem_of(name_key(original or described))}{_EDITED}"
    found = set(folder.stems.get(edited, ()))
    if original:
        found.add(original)
    return frozenset(found)


def is_edit_pair(first: str, second: str) -> bool:
    """Tell whether one file is the Takeout edited version of the other.

    Args:
        first: A file name.
        second: Another file name.

    Returns:
        True for `IMG_1234-edited.jpg` and `IMG_1234.jpg`, in either order.
    """
    for edited, other in ((first, second), (second, first)):
        original = edited_original(edited)
        if original and name_key(stem_of(original)) == name_key(stem_of(other)):
            return True
    return False


def edited_original(name: str) -> str | None:
    """Return the name of the original an edited Takeout version comes from.

    Args:
        name: A file name, `IMG_1234-edited.jpg`.

    Returns:
        `IMG_1234.jpg`, or None for a name that is not an edited version's.
    """
    path = PurePath(name)
    head, mark, _rest = path.stem.casefold().rpartition(_EDITED)
    if not mark or not head:
        return None
    return f"{path.stem[: len(head)]}{path.suffix}"


def _described(base: str) -> tuple[str, str]:
    """Split a `.json` name (without `.json`) into its photo's name and number.

    Args:
        base: `IMG_1234.jpg.supplemental-metada(1)`.

    Returns:
        `IMG_1234.jpg` and `(1)` (empty without a number).
    """
    number = ""
    found = _NUMBER.match(base)
    if found is not None:
        base, number = found["name"], found["number"]
    head, dot, last = base.rpartition(".")
    if dot and head and last and _METADATA_WORD.startswith(last.casefold()):
        base = head
    return base.rstrip("."), number


def _numbered(stem: str, number: str) -> str:
    """Put the number of a duplicate name back where the photo's name holds it.

    Args:
        stem: `IMG_1234.jpg`.
        number: `(1)`, or empty.

    Returns:
        `IMG_1234(1).jpg`.
    """
    if not number:
        return stem
    path = PurePath(stem)
    return f"{path.stem}{number}{path.suffix}"


def _original(described: str, folder: FolderNames, length: int) -> str | None:
    """Find the file a `.json` names: whole, without extension, or truncated.

    Args:
        described: The photo's name the `.json` gives.
        folder: The folder's files, indexed.
        length: The `.json` name's length: a long one may be truncated.

    Returns:
        The file's name, or None when none (or several) match.
    """
    key = name_key(described)
    if key in folder.keyed:
        return folder.keyed[key]
    by_stem = folder.stems.get(key, ())
    if len(by_stem) == 1:
        return by_stem[0]
    if length < TRUNCATED_FROM:
        return None
    started = [
        name
        for name in folder.starting(key)
        if _EDITED not in name_key(name)[len(key) :]
    ]
    return started[0] if len(started) == 1 else None
