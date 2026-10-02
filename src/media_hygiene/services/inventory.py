"""`inventory`: export what the audits learnt about every file, from the index alone.

No file of `/data` is opened: the rows come from `/cache/index.sqlite`. The export goes
to `<reports>/<stamp>-inventory/`, so both mounts must survive the container.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.dates import zone_of
from media_hygiene.constants import (
    INVENTORY_FILE_STEM,
    INVENTORY_FOLDER_SUFFIX,
    InventoryFormat,
)
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.index.listing import (
    count_files,
    indexed_files,
    shared_digests,
    walked_roots,
)
from media_hygiene.index.repository import FactsRepository
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.report.folders import new_report_folder
from media_hygiene.report.inventory_entries import InventoryContext, entry_of
from media_hygiene.report.inventory_workbook import (
    InventorySource,
    write_csv,
    write_workbook,
)
from media_hygiene.services.writable import writable_tip

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from media_hygiene.index.listing import WalkedRoot
    from media_hygiene.report.inventory_entries import Entry
    from media_hygiene.report.inventory_summary import InventorySummary
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class InventoryResult:
    """The file written, its counts, and how fresh each root is."""

    target: Path
    summary: InventorySummary
    roots: tuple[WalkedRoot, ...]


def export_inventory(runtime: Runtime, kind: InventoryFormat) -> InventoryResult:
    """Write the inventory of the index.

    Args:
        runtime: Settings, mount points and output.
        kind: Excel workbook or CSV file.

    Returns:
        What was written.

    Raises:
        MountError: No index to read, no reports folder to write to, or either
            failed.
    """
    index = _index_file(runtime)
    reports_dir = _reports_dir(runtime)
    try:
        with FactsRepository.open(index) as repository:
            connection = repository.connection
            if not count_files(connection):
                raise _no_index(runtime)
            roots = walked_roots(connection)
            source = InventorySource(
                _entries(runtime, connection),
                tuple((runtime.mapper.to_host(r.path), r.walked_at) for r in roots),
            )
            folder = new_report_folder(reports_dir, INVENTORY_FOLDER_SUFFIX)
            target = folder / f"{INVENTORY_FILE_STEM}.{kind.value}"
            summary = (
                write_csv(target, source)
                if kind is InventoryFormat.CSV
                else write_workbook(target, source)
            )
    except sqlite3.Error as exc:
        raise MountError(
            _("The index {file} cannot be read: {reason}.").format(
                file=runtime.mapper.to_host(index), reason=exc
            ),
            _("Delete it: the next audit builds it again, reading every file once."),
        ) from exc
    except OSError as exc:
        raise MountError(
            _("The inventory could not be written to {folder}: {reason}.").format(
                folder=runtime.mapper.to_host(reports_dir),
                reason=exc.strerror or exc,
            ),
            writable_tip((reports_dir,)) if isinstance(exc, PermissionError) else None,
        ) from exc
    return InventoryResult(target, summary, roots)


def _entries(runtime: Runtime, connection: sqlite3.Connection) -> Iterator[Entry]:
    """Stream the photos, RAW files and videos of the index.

    Args:
        runtime: Settings and host paths.
        connection: The open index.

    Yields:
        One entry per media file; other files (`--ext pdf`) are left out.
    """
    settings = runtime.settings
    context = InventoryContext(
        runtime.mapper,
        shared_digests(connection),
        settings.inventory,
        zone_of(settings.classify.timezone),
    )
    for file in indexed_files(connection):
        entry = entry_of(file, context)
        if entry is not None:
            yield entry


def _index_file(runtime: Runtime) -> Path:
    """The index to read, which must exist: opening a missing one would create it.

    Args:
        runtime: Mount points.

    Returns:
        Its path.

    Raises:
        MountError: The cache is not mounted, or holds no index yet.
    """
    index = runtime.index_file
    if index is None or not index.is_file():
        raise _no_index(runtime)
    return index


def _reports_dir(runtime: Runtime) -> Path:
    """The reports folder, which must survive the container.

    Args:
        runtime: Mount points.

    Returns:
        Its path.

    Raises:
        MountError: `/reports` is not mounted.
    """
    if not runtime.persistent(MountKind.REPORTS):
        raise MountError(
            _("No reports mount: the inventory would be lost with the container."),
            _('Add -v "<a folder of yours>:/reports" to get the inventory.'),
        )
    return runtime.locations.reports_dir


def _no_index(runtime: Runtime) -> MountError:
    """The error of an export without anything to export.

    Args:
        runtime: Mount points.

    Returns:
        The error, with the tip to run an audit first.
    """
    cache = runtime.mapper.to_host(runtime.locations.cache_dir)
    return MountError(
        _("No index in {folder}: nothing to export yet.").format(folder=cache),
        _(
            "Run 'audit' first with the same /cache mount: the inventory lists what"
            " the audits learnt, without reading the files again."
        ),
    )
