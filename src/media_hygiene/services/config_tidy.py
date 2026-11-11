"""`config tidy`: find the stale entries of `config.toml`, remove the ticked ones.

A dated copy of the file goes to `/cache/config-backups/` first (`/config` holds
`config.toml` only), the file is replaced atomically, then read back: what is shown as
removed is what the disk proves gone.
"""

from __future__ import annotations

import shutil
import sqlite3
import tomllib
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.own_events import folder_rules
from media_hygiene.config.tidy_find import TidyFindings, find_stale
from media_hygiene.config.tidy_rules import LibraryFacts
from media_hygiene.config.tidy_write import check_removed, without_entries
from media_hygiene.errors import MountError
from media_hygiene.file_history import replace_text
from media_hygiene.i18n import _
from media_hygiene.index.listing import indexed_files
from media_hygiene.index.read_only import connect_read_only
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import is_read_only
from media_hygiene.text_files import read_user_text

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.config.tidy_rules import StaleEntry
    from media_hygiene.services.runtime import Runtime

BACKUP_DIR: Final = "config-backups"
_STAMP: Final = "%Y%m%d-%H%M%S"
_ENCODING: Final = "utf-8"
_DAY: Final = 10  # `YYYY:MM:DD` at the start of an EXIF date


@dataclass(frozen=True, slots=True)
class Tidied:
    """What was removed, proven by reading the file back, and the copy kept."""

    removed: tuple[StaleEntry, ...]
    backup: Path


def stale_entries(runtime: Runtime) -> TidyFindings:
    """The stale entries of `config.toml`; none when there is no file.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The findings.
    """
    config_file = runtime.locations.config_file
    if not config_file.is_file():
        return TidyFindings((), ())
    document = tomllib.loads(read_user_text(config_file))
    return find_stale(document, library_facts(runtime), lambda p: _exists(runtime, p))


def library_facts(runtime: Runtime) -> LibraryFacts:
    """Read the host paths, cameras, days and named folders of the index.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The facts; empty without an index.
    """
    index_file = runtime.index_file
    if index_file is None or not index_file.is_file():
        return LibraryFacts()
    paths: list[str] = []
    shots: list[tuple[str, date | None]] = []
    named: set[str] = set()
    rules = folder_rules(runtime.settings.classify, ())
    try:
        with closing(connect_read_only(index_file)) as connection:
            for file in indexed_files(connection):
                host = runtime.mapper.to_host(file.path)
                paths.append(host)
                shots.append(_shot(file.facts.visual, file.facts.metadata))
                root = runtime.mounts.owner(file.path)
                if root is not None and rules.meaning(file.path.parent, root):
                    named.add(host)  # a folder `existing_folder` keeps
    except sqlite3.Error:
        return LibraryFacts()
    return LibraryFacts(tuple(paths), tuple(shots), frozenset(named))


def _shot(visual: object, metadata: object) -> tuple[str, date | None]:
    """A file's camera (as the `camera` rule reads it) and the day it was taken.

    Args:
        visual: Its `VisualFacts`, or None.
        metadata: Its `MediaMetadata`, or None.

    Returns:
        The camera text and the day, None when unknown.
    """
    names = (
        getattr(visual, "camera", None),
        getattr(metadata, "make", None),
        getattr(metadata, "model", None),
    )
    taken = getattr(visual, "taken_at", None)
    day: date | None = None
    if isinstance(taken, str):
        try:
            day = date.fromisoformat(taken[:_DAY].replace(":", "-"))
        except ValueError:
            day = None
    return " ".join(name for name in names if isinstance(name, str) and name), day


def _exists(runtime: Runtime, host: str) -> bool | None:
    """Tell whether a host folder exists; None when its drive is not mounted.

    Args:
        runtime: Settings, mount points and output.
        host: The folder, as `config.toml` writes it.

    Returns:
        True, False, or None (unknown).
    """
    container = runtime.mapper.to_container(host)
    owner = runtime.mounts.owner(container)
    if owner is None or owner == runtime.locations.data_dir:
        return None
    return container.is_dir()


def tidy(runtime: Runtime, entries: Sequence[StaleEntry]) -> Tidied:
    """Copy `config.toml` aside, remove the entries, read the file back.

    Args:
        runtime: Settings, mount points and output.
        entries: The entries to remove.

    Returns:
        What was removed and where the copy is.

    Raises:
        MountError: `/config` or `/cache` cannot be written.
    """
    writable(runtime)
    locations = runtime.locations
    config_file = locations.config_file
    text = read_user_text(config_file)
    result = without_entries(text, entries)
    backups = locations.cache_dir / BACKUP_DIR
    backups.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime(_STAMP)
    backup = backups / f"{config_file.name}.bak-{stamp}"
    shutil.copy2(config_file, backup)
    replace_text(config_file, result)
    check_removed(text, read_user_text(config_file), entries)  # proof, not promise
    return Tidied(tuple(entries), backup)


def writable(runtime: Runtime) -> None:
    """Refuse to write unless `/config` and `/cache` are mounted and writable.

    Args:
        runtime: Settings, mount points and output.

    Raises:
        MountError: One of them is not.
    """
    for kind in (MountKind.CONFIG, MountKind.CACHE):
        folder = runtime.locations.path_of(kind)
        if not runtime.persistent(kind) or is_read_only(folder):
            raise MountError(
                _("{folder} is not mounted, or read-only: nothing was written.").format(
                    folder=folder
                ),
                _("Mount it as for your other commands, without ':ro'."),
            )
