"""One way to name a photo in the user's files: `{path = '…', id = "…"}` (0551).

`id` is what media-hygiene trusts: the first 16 hex of the photo's SHA-256, a colon,
its size in bytes (collision odds for 100 000 files about 3·10⁻¹⁰, estimated n²/2⁶⁵,
lower with the size). `path` is the real host path, kept current: at once by the
tool's own moves (`follow_paths`), at the end of each `audit` for the renames made
outside (`relocate`: the id finds the file again). A photo edited since is another
photo: its id no longer matches, its path is left as it was. The files stay readable
by another program: a path anyone can open, and a content id anyone can recompute.
Places (`/config/places/`) use it, people and hand tags will (0555).
"""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import PureWindowsPath
from typing import TYPE_CHECKING, Any, Final

from pydantic import BaseModel, ConfigDict, Field, model_validator

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from pathlib import Path

PREFIX: Final = 16  # hex digits of the SHA-256 kept in an id
ID_PATTERN: Final = rf"^[0-9a-f]{{{PREFIX}}}:\d+$"
_LEGACY_SHA: Final = re.compile(r"^[0-9a-f]{64}$")
ENCODING: Final = "utf-8"


def content_id(sha256: str, size: int) -> str:
    """A photo's id: its digest's start and its size.

    Args:
        sha256: Its SHA-256, in hex.
        size: Its size in bytes.

    Returns:
        `<16 hex>:<size>`.
    """
    return f"{sha256[:PREFIX].lower()}:{size}"


def size_of(photo_id: str) -> int:
    """The size an id names.

    Args:
        photo_id: `<16 hex>:<size>`.

    Returns:
        The size in bytes.
    """
    return int(photo_id.rpartition(":")[2])


class PhotoRef(BaseModel):
    """A photo: where it is (for people and other programs), what it is (for us)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str = ""
    id: str = Field(pattern=ID_PATTERN)

    @model_validator(mode="before")
    @classmethod
    def _legacy(cls, data: Any) -> Any:  # noqa: ANN401 - pydantic's raw input
        """Read the form before 0551: `sha256` + `size` (+ `path`).

        Args:
            data: The raw entry.

        Returns:
            It, in today's form.
        """
        if isinstance(data, dict) and "sha256" in data and "id" not in data:
            rest = {k: v for k, v in data.items() if k not in {"sha256", "size"}}
            sha, size = str(data["sha256"]), data.get("size", 0)
            if _LEGACY_SHA.match(sha) and isinstance(size, int):
                return {**rest, "id": content_id(sha, size)}
        return data


def follow_paths[R: PhotoRef](refs: Iterable[R], moves: Mapping[str, str]) -> list[R]:
    """The references, each path followed through the moves (A → B → C).

    Args:
        refs: The references.
        moves: New host path by old one (a quarantine then back loops home).

    Returns:
        Them, in order, those moved with their new path.
    """
    followed: list[R] = []
    for ref in refs:
        path, seen = ref.path, {ref.path}
        while (path := moves.get(path, path)) not in seen:
            seen.add(path)
        followed.append(
            ref if path == ref.path else ref.model_copy(update={"path": path})
        )
    return followed


def relocate[R: PhotoRef](
    refs: Iterable[R], found: Mapping[str, Sequence[str]]
) -> list[R]:
    """The references whose file was renamed outside, their path rewritten by id.

    A path still among the files of its id stays (a copy on another drive changes
    nothing); an id found nowhere keeps its path (not mounted, edited, deleted).
    Between identical copies, the one of the same file name wins, then the first by
    path: the same answer on every run.

    Args:
        refs: The references.
        found: The host paths holding each id, as the audit saw them.

    Returns:
        Them, in order.
    """
    placed: list[R] = []
    for ref in refs:
        paths = sorted(found.get(ref.id, ()))
        if not paths or ref.path in paths:
            placed.append(ref)
            continue
        name = PureWindowsPath(ref.path).name.casefold()
        same = [path for path in paths if PureWindowsPath(path).name.casefold() == name]
        placed.append(ref.model_copy(update={"path": (same or paths)[0]}))
    return placed


def ref_line(ref: PhotoRef, extra: Mapping[str, int] | None = None) -> str:
    """One reference as a TOML inline table: `{path = '…', id = "…"}`.

    Args:
        ref: The reference.
        extra: More integer keys (a face number).

    Returns:
        The table's text.
    """
    parts = [f"path = {quoted(ref.path)}", f'id = "{ref.id}"']
    parts.extend(f"{key} = {value}" for key, value in (extra or {}).items())
    return "{" + ", ".join(parts) + "}"


def quoted(value: str) -> str:
    r"""A TOML string: literal ('C:\Photos') when it can be one, else basic.

    Args:
        value: The text.

    Returns:
        It, quoted.
    """
    if "'" not in value and not any(ord(c) < 0x20 or ord(c) == 0x7F for c in value):  # noqa: PLR2004
        return f"'{value}'"
    return json.dumps(value, ensure_ascii=False).replace("\x7f", "\\u007f")


def write_refs(path: Path, header: str, lines: Mapping[str, Sequence[str]]) -> None:
    """Replace a file of references atomically, then read it back.

    Args:
        path: The file.
        header: The comment on its first line.
        lines: Each array's inline tables, by key.

    Raises:
        ValueError: The text written does not read back (never expected).
        OSError: The file cannot be written.
    """
    text = [f"# {' '.join(header.split())}"]
    for key, rows in lines.items():
        text.append(f"{key} = [")
        text.extend(f"    {row}," for row in rows)
        text.append("]")
    content = "\n".join(text) + "\n"
    if path.is_file() and path.read_text(ENCODING) == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(content, ENCODING)
    temporary.replace(path)
    if tomllib.loads(path.read_text(ENCODING)).keys() != lines.keys():
        message = f"{path} did not read back"
        raise ValueError(message)
