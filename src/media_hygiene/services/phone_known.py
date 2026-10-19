r"""What the container knows of the files named like a phone's: index, journals, folder.

Three places, each matched by name (case ignored) and size, the only facts the phone
gives (0219): the index (the library as the last audits saw it, folders not plugged
in now included), the journals (a file set aside by a choice, its run's quarantine
still there or purged) and the destination folder of the import. Between several
files of the same name and size, the first path in alphabetical order is named, and
the latest set-aside: the same answer on every run.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from itertools import chain
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.purge import runs_in
from media_hygiene.i18n import _
from media_hygiene.index.repository import FactsRepository
from media_hygiene.services.phone_plan import AsideState, Known, SetAside
from media_hygiene.services.quarantines import mounted_quarantines
from media_hygiene.services.returned import remembered_of

if TYPE_CHECKING:
    import sqlite3

    from media_hygiene.plan.returned import Remembered
    from media_hygiene.services.phone_plan import NameKey, PhoneFile
    from media_hygiene.services.runtime import Runtime

_FILES: Final = "SELECT path, size FROM files"
# `mh` copies into `<destination>\.mh-phone-<run>` first: never a file of the library.
STAGING_PREFIX: Final = ".mh-phone-"


@dataclass(frozen=True, slots=True)
class PhoneQuery:
    """The files of the phone, and the destination in the container (None: none)."""

    files: tuple[PhoneFile, ...]
    destination: Path | None = None


def known_of(runtime: Runtime, query: PhoneQuery) -> Known:
    """Gather what the library, the journals and the destination hold of those files.

    Args:
        runtime: Settings, mount points and output.
        query: The files of the phone and the destination.

    Returns:
        The files of the same name and size, in each place.
    """
    wanted = frozenset(file.key for file in query.files)
    with FactsRepository.open(runtime.index_file) as repository:
        connection = repository.connection
        library = _library(runtime, connection, wanted)
        aside = _set_aside(runtime, connection, wanted)
    destination = query.destination
    return Known(
        library=MappingProxyType(library),
        set_aside=MappingProxyType(aside),
        destination=MappingProxyType(
            _in_folder(destination, wanted) if destination is not None else {}
        ),
    )


def _library(
    runtime: Runtime, connection: sqlite3.Connection, wanted: frozenset[NameKey]
) -> dict[NameKey, str]:
    """Find the files of the index named like the phone's, of the same size.

    Args:
        runtime: Settings, mount points and output (host paths, the warning).
        connection: The index.
        wanted: The names and sizes of the phone.

    Returns:
        The host path of the first match of each, in path order.
    """
    sizes = {size for _name, size in wanted}
    found: dict[NameKey, str] = {}
    rows = 0
    for path, size in connection.execute(_FILES):
        rows += 1
        if size not in sizes or STAGING_PREFIX in path:
            continue
        key = (PurePosixPath(path).name.casefold(), int(size))
        if key in wanted and (key not in found or path < found[key]):
            found[key] = path
    if not rows:
        runtime.output.warning(
            _(
                "The cache knows no photo yet: type mh audit first, or every photo "
                "of the phone is taken for new."
            )
        )
    return {key: runtime.mapper.to_host(Path(path)) for key, path in found.items()}


def _set_aside(
    runtime: Runtime, connection: sqlite3.Connection, wanted: frozenset[NameKey]
) -> dict[NameKey, SetAside]:
    """Find the files set aside by a choice named like the phone's, of the same size.

    Args:
        runtime: Settings, mount points and the journal.
        connection: The index, keeping what each journal said.
        wanted: The names and sizes of the phone.

    Returns:
        The latest set-aside of each, with its run's quarantine state.
    """
    remembered = remembered_of(runtime, connection)
    held = frozenset(runs_in(mounted_quarantines(runtime).folders))
    found: dict[NameKey, Remembered] = {}
    pairs = chain(remembered.by_digest.items(), remembered.by_partial.items())
    for (size, _digest), said in pairs:
        key = (PureWindowsPath(said.host_path).name.casefold(), size)
        if key not in wanted:
            continue
        last = found.get(key)
        if last is None or (said.at, said.run_id) > (last.at, last.run_id):
            found[key] = said
    return {
        key: SetAside(
            said.run_id,
            said.at,
            said.action.value,
            AsideState.QUARANTINE if said.run_id in held else AsideState.PURGED,
        )
        for key, said in found.items()
    }


def _in_folder(folder: Path, wanted: frozenset[NameKey]) -> dict[NameKey, str]:
    """Find the files of the destination named like the phone's, of the same size.

    Args:
        folder: The destination in the container; missing: nothing there.
        wanted: The names and sizes of the phone.

    Returns:
        The path of the first match of each, relative to the folder, in walk order.
    """
    found: dict[NameKey, str] = {}
    for root, folders, names in os.walk(folder):
        folders[:] = sorted(
            name for name in folders if not name.startswith(STAGING_PREFIX)
        )
        for name in sorted(names):
            path = Path(root) / name
            try:
                size = path.stat().st_size
            except OSError:
                continue
            key = (name.casefold(), size)
            if key in wanted and key not in found:
                found[key] = path.relative_to(folder).as_posix()
    return found
