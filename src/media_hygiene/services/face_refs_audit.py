"""At the end of an `audit`: the named faces follow their photos by id (0570).

Each file of `/config/people/` is read as written. A face `{path, id, face}` whose
id the index holds elsewhere (a folder renamed in Explorer) gets the new path; one
whose id is found nowhere while its path now holds another content (an edited photo,
another photo) loses its name; one not found at all (not mounted) stays. A face still
in the form before 0570 (`<path>#<n>`) gets its id: the index's digest, else its
photo read once (0635, `face_ids_read`). A file changed is replaced atomically and
read back.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.config.face_refs import (
    FACE,
    FaceRef,
    container_of,
    face_line,
    split_key,
)
from media_hygiene.config.people_files import ENCODING, FACES, FOLDER, REJECTED
from media_hygiene.config.photo_ref import relocate, write_refs
from media_hygiene.services.face_ids_read import FaceIdReader

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from media_hygiene.paths.host_paths import HostPathMapper

_PATTERN: Final = "*.toml"
_COMMENT: Final = "#"


@dataclass(frozen=True, slots=True)
class FaceSources:
    """What the audit knows: the paths of each id, the mapping, the index's digests."""

    found: Mapping[str, Sequence[str]]  # host paths by id
    mapper: HostPathMapper
    reader: FaceIdReader = field(default_factory=FaceIdReader)


@dataclass(slots=True)
class FaceTally:
    """The faces changed by the audit, counted on the files read back."""

    moved: int = 0
    dropped: int = 0
    identified: int = 0
    files: list[Path] = field(default_factory=list)


def face_files(config_dir: Path) -> list[Path]:
    """The people's files.

    Args:
        config_dir: The folder of `config.toml`.

    Returns:
        Them, sorted.
    """
    return sorted((config_dir / FOLDER).glob(_PATTERN))


def wanted_ids(files: Sequence[Path]) -> frozenset[str]:
    """The ids written in the people's files.

    Args:
        files: The files.

    Returns:
        Every id of a face table.
    """
    ids: set[str] = set()
    for file in files:
        loaded = tomllib.loads(file.read_text(ENCODING))
        for key in (FACES, REJECTED):
            value = loaded.get(key, [])
            entries = value if isinstance(value, list) else []
            ids.update(
                str(e["id"]) for e in entries if isinstance(e, dict) and "id" in e
            )
    return frozenset(ids)


def checked_path(entry: object, sources: FaceSources) -> Path | None:
    """The photo whose content decides what becomes of a face.

    Args:
        entry: As loaded.
        sources: The ids found, the mapping.

    Returns:
        Its container path; None when the ids found already decide.
    """
    if isinstance(entry, dict) and FACE in entry:
        ref = FaceRef.model_validate(entry)
        if ref.id in sources.found:
            return None
        return container_of(ref.path, sources.mapper)
    parts = split_key(str(entry))
    return None if parts is None else Path(parts[0])


def _entry(entry: object, sources: FaceSources, tally: FaceTally) -> str | None:
    """One face as it is written after the audit.

    Args:
        entry: As loaded.
        sources: The ids found, the mapping.
        tally: Counted here.

    Returns:
        Its line; None when the face loses its name.
    """
    mapper = sources.mapper
    if isinstance(entry, dict) and FACE in entry:
        ref = FaceRef.model_validate(entry)
        placed = relocate([ref], sources.found)[0]
        if placed.path != ref.path:
            tally.moved += 1
        elif (checked := checked_path(entry, sources)) is not None:
            now = sources.reader.current_id(checked)
            if now is not None and now != ref.id:
                tally.dropped += 1
                return None
        key = f"{container_of(placed.path, mapper)}#{placed.face}"
        return face_line(
            key, {str(container_of(placed.path, mapper)): placed.id}, mapper
        )
    key = str(entry)
    parts = split_key(key)
    photo_id = None if parts is None else sources.reader.current_id(Path(parts[0]))
    if parts is None or photo_id is None:
        return face_line(key, {}, mapper)
    tally.identified += 1
    return face_line(key, {parts[0]: photo_id}, mapper)


def rewrite_file(file: Path, sources: FaceSources, tally: FaceTally) -> None:
    """Rewrite one people's file when a face changed.

    Args:
        file: The file.
        sources: The ids found, the mapping.
        tally: Counted here; the file added when rewritten.
    """
    text = file.read_text(ENCODING)
    loaded = tomllib.loads(text)
    first = text.split("\n", 1)[0]
    header = first.removeprefix(_COMMENT).strip() if first.startswith(_COMMENT) else ""
    before = (tally.moved, tally.dropped, tally.identified)
    lines: dict[str, list[str]] = {}
    for key in (FACES, REJECTED):
        value = loaded.get(key)
        if isinstance(value, list):
            rows = (_entry(entry, sources, tally) for entry in value)
            lines[key] = [row for row in rows if row is not None]
    if (tally.moved, tally.dropped, tally.identified) != before:
        write_refs(file, header, lines)
        tally.files.append(file)
