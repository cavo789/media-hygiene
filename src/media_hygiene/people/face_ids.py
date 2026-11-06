"""The content id of each photo with a named face, for its file (0570).

A save rewrites the people's files from the settings, which hold container paths
only: the ids come from the files as they are (by container path, a run's moves
followed), else from the index's full digest. Nothing is read from the photos here:
a save stays instant; a face whose id is still unknown is written as before 0570,
and the next `audit` gives it its id (`services.face_refs_audit`).
"""

from __future__ import annotations

import contextlib
import sqlite3
import tomllib
from typing import TYPE_CHECKING, Final

from media_hygiene.config.face_refs import face_mapper, ids_by_key, split_key
from media_hygiene.config.people_files import ENCODING, FACES, FOLDER, REJECTED
from media_hygiene.config.photo_ref import content_id
from media_hygiene.paths.locations import Locations

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper

_ROW: Final = "SELECT size, full_digest FROM files WHERE path = ?"
_PATTERN: Final = "*.toml"


def written_ids(config_dir: Path, mapper: HostPathMapper) -> dict[str, str]:
    """The ids the people's files hold now, by container path.

    Args:
        config_dir: The folder of `config.toml`.
        mapper: Host ↔ container.

    Returns:
        Id by container path; a file that does not load is skipped.
    """
    ids: dict[str, str] = {}
    for file in sorted((config_dir / FOLDER).glob(_PATTERN)):
        try:
            loaded = tomllib.loads(file.read_text(ENCODING))
            for key in (FACES, REJECTED):
                value = loaded.get(key, [])
                ids.update(ids_by_key(value if isinstance(value, list) else [], mapper))
        except OSError, ValueError:
            continue
    return ids


def known_ids(
    config_dir: Path, keys: Iterable[str], moves: Mapping[str, str] | None = None
) -> dict[str, str]:
    """The id of every face's photo that can be known without reading it.

    Args:
        config_dir: The folder of `config.toml`.
        keys: The faces to write, `<container path>#<n>`.
        moves: New container path by old one (a run's moves): the id follows.

    Returns:
        Id by container path.
    """
    ids = written_ids(config_dir, face_mapper())
    for old, new in (moves or {}).items():
        if old in ids:
            ids.setdefault(new, ids[old])
    paths = {parts[0] for key in keys if (parts := split_key(key)) is not None}
    missing = sorted(paths - ids.keys())
    if missing:
        ids.update(index_ids(missing))
    return ids


def index_ids(paths: Iterable[str]) -> dict[str, str]:
    """The ids the index knows (a full digest), by container path.

    Args:
        paths: Container paths.

    Returns:
        Id by path; empty without an index.
    """
    index = Locations().index_file
    if not index.is_file():
        return {}
    found: dict[str, str] = {}
    with contextlib.suppress(sqlite3.Error):
        connection = sqlite3.connect(f"file:{index}?mode=ro", uri=True)
        try:
            for path in paths:
                row = connection.execute(_ROW, (path,)).fetchone()
                if row is not None and row[1]:
                    found[path] = content_id(str(row[1]), int(row[0]))
        finally:
            connection.close()
    return found
