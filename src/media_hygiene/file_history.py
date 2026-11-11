"""Previous versions of the user's own files, kept at each save (0691).

Every save of `config.toml`, `/config/people/<name>.toml`, `/config/events/<year>.toml`
and `albums.json` goes through `replace_text`: the new content is written to a draft,
the current file is copied into `.history/` first, then the draft takes its name. The
versions of a file under `/config` live in `/config/.history/<relative path>.<stamp>`
(the folder holding `config.toml`; `mh backup` archives them with the rest), those of
another file (`albums.json` in `/reports`) in `.history/` beside it. A version name ends
with its stamp, never with `.toml` or `.json`: no reader of these folders mistakes it
for a live file. Each file keeps its `KEEP_VERSIONS` newest versions, none older than
`KEEP_DAYS` but the newest, trimmed at save time.
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import CONFIG_FILE_NAME

if TYPE_CHECKING:
    from pathlib import Path

HISTORY_DIR: Final = ".history"
KEEP_VERSIONS: Final = 20
KEEP_DAYS: Final = 30
_STAMP: Final = "%Y%m%dT%H%M%S%fZ"
_ENCODING: Final = "utf-8"


def history_root(path: Path) -> Path:
    """Return the folder whose `.history/` holds the versions of a file.

    Args:
        path: A file saved by the tool.

    Returns:
        The nearest folder holding `config.toml` (two levels up at most), else the
        file's own folder.
    """
    for folder in (path.parent, path.parent.parent):
        if (folder / CONFIG_FILE_NAME).is_file():
            return folder
    return path.parent


def _prefix(path: Path) -> tuple[Path, str]:
    root = history_root(path)
    relative = path.relative_to(root)
    return root / HISTORY_DIR / relative.parent, f"{relative.name}."


def versions_of(path: Path) -> tuple[Path, ...]:
    """List the previous versions of a file, newest first.

    Args:
        path: A file saved by the tool.

    Returns:
        Its versions; none when nothing was saved over it.
    """
    folder, prefix = _prefix(path)
    if not folder.is_dir():
        return ()
    found = [
        each
        for each in folder.iterdir()
        if each.is_file() and _stamp_of(each.name, prefix) is not None
    ]
    return tuple(sorted(found, key=lambda each: each.name, reverse=True))


def _stamp_of(name: str, prefix: str) -> datetime | None:
    if not name.startswith(prefix):
        return None
    try:
        return datetime.strptime(name.removeprefix(prefix), _STAMP).replace(tzinfo=UTC)
    except ValueError:
        return None


def keep_previous(path: Path) -> Path | None:
    """Copy the current file into its history, then trim the history.

    Args:
        path: The file about to be replaced.

    Returns:
        The version written; None when there was no file yet.
    """
    if not path.is_file():
        return None
    folder, prefix = _prefix(path)
    folder.mkdir(parents=True, exist_ok=True)
    now = datetime.now(tz=UTC)
    version = folder / f"{prefix}{now.strftime(_STAMP)}"
    shutil.copy2(path, version)
    _trim(versions_of(path), prefix, now)
    return version


def _trim(versions: tuple[Path, ...], prefix: str, now: datetime) -> None:
    oldest = now - timedelta(days=KEEP_DAYS)
    for rank, version in enumerate(versions):
        stamp = _stamp_of(version.name, prefix)
        if rank >= KEEP_VERSIONS or (rank and stamp is not None and stamp < oldest):
            version.unlink(missing_ok=True)


def replace_text(path: Path, text: str) -> None:
    """Save a file atomically, its current content kept as a version first.

    An unchanged content writes no version (a save that changes nothing).

    Args:
        path: The file to write.
        text: Its new content, written in UTF-8.
    """
    draft = path.with_name(f".{path.name}.tmp")
    draft.write_text(text, _ENCODING)
    if path.is_file() and path.read_bytes() == draft.read_bytes():
        draft.replace(path)
        return
    keep_previous(path)
    draft.replace(path)


def restore_version(path: Path, version: Path) -> bytes:
    """Put a previous version back, the current content kept as a version first.

    Args:
        path: The file to restore.
        version: One of `versions_of(path)`.

    Returns:
        The content read back from the file.

    Raises:
        ValueError: The version is not one of this file's.
        OSError: The file read back differs from the version.
    """
    if version not in versions_of(path):
        msg = f"{version} is not a version of {path}"
        raise ValueError(msg)
    wanted = version.read_bytes()
    draft = path.with_name(f".{path.name}.tmp")
    draft.write_bytes(wanted)
    keep_previous(path)
    draft.replace(path)
    back = path.read_bytes()  # proof, not promise
    if back != wanted:
        msg = f"{path} differs from {version} after the restore"
        raise OSError(msg)
    return back
