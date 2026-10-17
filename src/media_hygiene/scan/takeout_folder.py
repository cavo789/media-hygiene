"""The names of one folder, indexed once to find the files Takeout `.json` describe.

A Takeout year folder holds thousands of photos and as many `.json` files: looking
each `.json`'s photo up among every name would make the walk quadratic (2 s for 500
photos, measured). The folder's names are indexed once, by whole name, by name
without extension and in order (for the names Google truncated).
"""

from __future__ import annotations

import bisect
import functools
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import SIDECAR_EXTENSIONS

if TYPE_CHECKING:
    from collections.abc import Mapping

JSON_SUFFIX: Final = ".json"
_REPLACED: Final = str.maketrans({"&": "_", "?": "_"})
# After the last possible key: the end of a prefix range.
_AFTER: Final = "\U0010ffff"
# The folders indexed lately: a walk asks for the same folder once per `.json`.
_REMEMBERED: Final = 8
_NOT_MEDIA: Final = frozenset({JSON_SUFFIX, *SIDECAR_EXTENSIONS})


def name_key(name: str) -> str:
    """The form names are compared in: any case, `&` and `?` as Google writes them.

    Args:
        name: A file name.

    Returns:
        Its key.
    """
    return name.translate(_REPLACED).casefold()


def stem_of(name: str) -> str:
    """A name without its extension (`.hidden` stays whole).

    Args:
        name: A file name.

    Returns:
        Its stem.
    """
    head, dot, _extension = name.rpartition(".")
    return head if dot and head else name


@dataclass(frozen=True, slots=True)
class FolderNames:
    """The media names of a folder, by key, by stem key, and their keys in order."""

    keyed: Mapping[str, str]
    stems: Mapping[str, tuple[str, ...]]
    ordered: tuple[str, ...]

    def starting(self, prefix: str) -> list[str]:
        """The names whose key starts with `prefix`.

        Args:
            prefix: A key's beginning.

        Returns:
            Those names, in key order.
        """
        first = bisect.bisect_left(self.ordered, prefix)
        last = bisect.bisect_left(self.ordered, prefix + _AFTER)
        return [self.keyed[key] for key in self.ordered[first:last]]


@functools.lru_cache(maxsize=_REMEMBERED)
def folder_names(names: tuple[str, ...]) -> FolderNames:
    """Index the names of a folder, `.json` files and other sidecars left out.

    Args:
        names: Every file name of the folder.

    Returns:
        The index.
    """
    keyed = {
        name_key(name): name
        for name in names
        if f".{name.rpartition('.')[2].casefold()}" not in _NOT_MEDIA
    }
    stems: dict[str, list[str]] = {}
    for key, name in keyed.items():
        stems.setdefault(stem_of(key), []).append(name)
    return FolderNames(
        keyed,
        {stem: tuple(found) for stem, found in stems.items()},
        tuple(sorted(keyed)),
    )
