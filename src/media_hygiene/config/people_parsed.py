"""A person's file as the pages need it: its lists as settings keys, its photos' ids.

Made once per version of the file (`stamped_value`): turning 12 000 Windows paths
into container keys, twice per save, was the larger part of a naming once the TOML
itself was kept (measured here on 60 files, 1.3 MB: 0.35 s per save, 2026-11-15).
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.config.face_refs import face_keys, face_mapper, ids_by_key
from media_hygiene.config.stamped_text import stamped_value

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

FACES: Final = "faces"
REJECTED: Final = "rejected"
LISTS: Final = (FACES, REJECTED)


@dataclass(frozen=True, slots=True)
class ParsedFile:
    """A file's lists (settings keys, or what is malformed), its ids by path."""

    lists: Mapping[str, tuple[object, ...]]
    ids: Mapping[str, str]


def parsed_file(path: Path) -> ParsedFile:
    """A person's file, parsed again only once it changed.

    Args:
        path: The file.

    Returns:
        Its lists and ids; shared between callers, never to change.

    Raises:
        OSError: The file cannot be read (missing included).
        UnicodeDecodeError: It is not UTF-8.
        tomllib.TOMLDecodeError: It is not TOML.
    """
    return stamped_value(path, _parse)


def _parse(text: str) -> ParsedFile:
    """Parse a person's file.

    Args:
        text: Its text.

    Returns:
        Its lists and ids.
    """
    loaded = tomllib.loads(text)
    mapper = face_mapper()
    lists: dict[str, tuple[object, ...]] = {}
    ids: dict[str, str] = {}
    for key in LISTS:
        value = loaded.get(key, [])
        if not isinstance(value, list):  # malformed: the settings say what is wrong
            lists[key] = (value,)
            continue
        lists[key] = tuple(face_keys(value, mapper))
        ids.update(ids_by_key(value, mapper))
    return ParsedFile(lists, ids)
