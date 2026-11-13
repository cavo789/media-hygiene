"""The *Versions* page's facts (0784): each file saved by the tool, its versions kept.

The files are found from the `.history/` folders themselves (`/config/.history/` and
`albums.json`'s beside it), so a file a later release starts saving is listed with no
change here. Each version says which keys differ from the content that replaced it (the
next newer version, or the file as it is now). A restore goes through
`file_history.restore_version`: the current content kept as a version first (the
restore is itself undoable), the file read back and returned.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.file_history import HISTORY_DIR, restore_version, versions_of
from media_hygiene.share.albums import ALBUMS_FILE

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

_FROZEN: Final = ConfigDict(frozen=True, extra="forbid")
_SHOWN_KEYS: Final = 8  # the keys named per version; the others counted
_ENCODING: Final = "utf-8"
_UNREADABLE: Final = "?"  # a version that does not parse: its keys are unknown


class Version(BaseModel):
    """One version kept: its name (its stamp), its size, the keys it differs by."""

    model_config = _FROZEN

    name: str
    when: str  # ISO, UTC
    size: int
    keys: tuple[str, ...]
    more: int  # keys changed beyond those named


class SavedFile(BaseModel):
    """A file saved by the tool and its versions, newest first."""

    model_config = _FROZEN

    path: str  # inside the container, the key a restore names
    label: str  # relative to its folder, as the page names it
    versions: tuple[Version, ...]


def saved_files(locations: Locations) -> tuple[SavedFile, ...]:
    """Every file with a version kept, `config.toml` first.

    Args:
        locations: The mount points.

    Returns:
        Them.
    """
    found: dict[Path, str] = {}
    for root in (locations.config_dir, locations.reports_dir):
        history = root / HISTORY_DIR
        if not history.is_dir():
            continue
        for kept in sorted(history.rglob("*")):
            if kept.is_file():
                relative = kept.relative_to(history)
                live = root / relative.parent / relative.name.rsplit(".", 1)[0]
                found.setdefault(live, str(live.relative_to(root)))
    files = [_file(path, label) for path, label in found.items()]
    files = [each for each in files if each.versions]
    files.sort(key=lambda each: (each.path != str(locations.config_file), each.label))
    return tuple(files)


def _file(path: Path, label: str) -> SavedFile:
    kept = versions_of(path)
    following: bytes | None = path.read_bytes() if path.is_file() else None
    versions = []
    for version in kept:
        content = version.read_bytes()
        keys = _changed(path.name, content, following)
        versions.append(
            Version(
                name=version.name,
                when=version.name.rsplit(".", 1)[1],
                size=len(content),
                keys=keys[:_SHOWN_KEYS],
                more=max(0, len(keys) - _SHOWN_KEYS),
            )
        )
        following = content
    return SavedFile(path=str(path), label=label, versions=tuple(versions))


def _changed(name: str, older: bytes, newer: bytes | None) -> tuple[str, ...]:
    """The keys that differ between a version and what replaced it.

    Args:
        name: The file's name (its kind: `.json` or TOML).
        older: The version.
        newer: What replaced it; None: the file is gone.

    Returns:
        The dotted keys, sorted; `?` when one side does not parse.
    """
    if newer is None:
        return ()
    try:
        before, after = _flat(name, older), _flat(name, newer)
    except ValueError, UnicodeDecodeError:
        return (_UNREADABLE,)
    return tuple(
        sorted(
            key
            for key in before.keys() | after.keys()
            if before.get(key) != after.get(key)
        )
    )


def _flat(name: str, content: bytes) -> dict[str, str]:
    text = content.decode(_ENCODING)
    data: object = json.loads(text) if name == ALBUMS_FILE else tomllib.loads(text)
    flat: dict[str, str] = {}
    _walk(data, "", flat)
    return flat


def _walk(data: object, prefix: str, flat: dict[str, str]) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            _walk(value, f"{prefix}.{key}" if prefix else str(key), flat)
        return
    flat[prefix or "."] = json.dumps(data, sort_keys=True, default=str)


def restore_named(locations: Locations, path: str, name: str) -> tuple[bytes, str]:
    """Put a version back, by the names the page shows.

    Args:
        locations: The mount points.
        path: The file, as `saved_files` named it (never any other path).
        name: The version's name.

    Returns:
        The content read back from the file, and the name of the version that now
        keeps what it held (the Undo of this restore).

    Raises:
        LookupError: The file or the version is not kept (any more): nothing changed.
    """
    listed = {each.path for each in saved_files(locations)}
    if path not in listed:
        raise LookupError(path)
    live = Path(path)
    version = next((each for each in versions_of(live) if each.name == name), None)
    if version is None:
        raise LookupError(name)
    back = restore_version(live, version)
    return back, versions_of(live)[0].name
