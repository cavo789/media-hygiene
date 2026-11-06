r"""A named face in `people/*.toml`: `{path = '…', id = "…", face = n}` (0570).

The settings keep each face as `<container path>#<n>`: every reader of `[people]`
works on that. The files hold the photo the way places do (`photo_ref`, 0551): the
host path the user knows (`C:\Photos\…`), the content id that finds it again after a
rename made outside the tool, and the face number. The form before 0570, the bare
`<path>#<n>` string, still loads, and is written back as it was while its id is not
known (the next `audit` gives it one).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Final

from pydantic import Field

from media_hygiene.config.photo_ref import PhotoRef, ref_line
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.paths.locations import Locations
from media_hygiene.paths.mounts import MountTable

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

SEPARATOR: Final = "#"
FACE: Final = "face"


class FaceRef(PhotoRef):
    """A face: its photo (path, id) and its number on it."""

    face: int = Field(ge=0)


def face_mapper() -> HostPathMapper:
    """The host ↔ container mapping of this run.

    Returns:
        It, from the mount table.
    """
    return HostPathMapper(Locations().data_dir, MountTable.current().host_sources)


def split_key(key: str) -> tuple[str, int] | None:
    """A face key's container path and number.

    Args:
        key: `<container path>#<n>`.

    Returns:
        Both; None when the key is not of that form.
    """
    path, separator, number = key.rpartition(SEPARATOR)
    if not separator or not number.isdigit():
        return None
    return path, int(number)


def container_of(path: str, mapper: HostPathMapper) -> Path:
    """Where a face's photo is in the container; a set-aside one stays as written.

    A photo in the quarantine is written with its container path (it has no host
    path of the data folders): read back as it is, not as a folder of `/data`.

    Args:
        path: As written in the file.
        mapper: Host ↔ container.

    Returns:
        The container path.
    """
    if path.startswith("/") and Path(path).is_relative_to(Locations().quarantine_dir):
        return Path(path)
    return mapper.to_container(path)


def key_of(ref: FaceRef, mapper: HostPathMapper) -> str:
    """The settings' key of a face read from a file.

    Args:
        ref: The face.
        mapper: Host ↔ container.

    Returns:
        `<container path>#<n>`.
    """
    return f"{container_of(ref.path, mapper)}{SEPARATOR}{ref.face}"


def face_keys(entries: Iterable[object], mapper: HostPathMapper | None) -> list[object]:
    """The entries of a file as the settings read them: tables become keys.

    Args:
        entries: The array as loaded (strings, tables, or anything malformed).
        mapper: Host ↔ container; None: made on the first table met.

    Returns:
        Strings for the faces; whatever else is left for the settings to refuse.
    """
    keys: list[object] = []
    for entry in entries:
        if isinstance(entry, dict) and FACE in entry:
            mapper = mapper or face_mapper()
            keys.append(key_of(FaceRef.model_validate(entry), mapper))
        else:
            keys.append(entry)
    return keys


def ids_by_key(entries: Iterable[object], mapper: HostPathMapper) -> dict[str, str]:
    """The content id of each container path written as a table.

    Args:
        entries: The array as loaded.
        mapper: Host ↔ container.

    Returns:
        Id by container path.
    """
    ids: dict[str, str] = {}
    for entry in entries:
        if isinstance(entry, dict) and FACE in entry:
            ref = FaceRef.model_validate(entry)
            ids[str(container_of(ref.path, mapper))] = ref.id
    return ids


def face_line(key: str, ids: Mapping[str, str], mapper: HostPathMapper) -> str:
    """One face as written in its file: a table when its id is known.

    Args:
        key: `<container path>#<n>`.
        ids: Id by container path.
        mapper: Host ↔ container.

    Returns:
        `{path = '…', id = "…", face = n}`, else the key quoted as before 0570.
    """
    parts = split_key(key)
    photo_id = ids.get(parts[0]) if parts is not None else None
    if parts is None or photo_id is None:
        return json.dumps(key, ensure_ascii=False).replace("\x7f", "\\u007f")
    ref = FaceRef(path=mapper.to_host(Path(parts[0])), id=photo_id, face=parts[1])
    return ref_line(ref, {FACE: ref.face})
