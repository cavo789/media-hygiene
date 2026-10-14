"""Walk the data roots, taking from the index the folders that did not change.

Shared by `audit` and `classify`. Without a persistent `/cache`, or with
`[scan] full_check_days = 0` (`audit --full`), every folder is read. The index keeps
the listings of the folders read, for the next walk.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext
from media_hygiene.index.folder_listings import load_listings, save_listings
from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan.folder_cache import WalkSetup
from media_hygiene.scan.walker import Walk, walk
from media_hygiene.services.policy import scan_filters

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.index.pruning import Pruned
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime


def list_media(
    runtime: Runtime, roots: tuple[Path, ...], progress: ProgressSink
) -> Walk:
    """Walk the roots, reusing the listings the index may be trusted for.

    Args:
        runtime: Settings, the index file, output.
        roots: The mounted folders.
        progress: Advanced once per media file found.

    Returns:
        What the walk found.
    """
    filters = scan_filters(runtime.settings, runtime.mapper)
    index = runtime.index_file
    if index is None:
        found = asyncio.run(walk(roots, WalkSetup(filters), progress))
        _tell(runtime, found)
        return found
    days = runtime.settings.scan.full_check_days
    existed = index.is_file()
    with FactsRepository.open(index) as repository:  # one connection for both
        setup = WalkSetup(filters)
        if existed and days:
            known = load_listings(repository.connection, roots)
            trusted = datetime.now(UTC) - timedelta(days=days)
            setup = WalkSetup(filters, known, trusted)
        found = asyncio.run(walk(roots, setup, progress))
        save_listings(repository.connection, found.listings, (roots, found.visited))
    _tell(runtime, found)
    return found


def _tell(runtime: Runtime, found: Walk) -> None:
    """Say how many folders came from the index, and how to read everything.

    Args:
        runtime: Settings and output.
        found: What the walk found.
    """
    if not found.reused:
        return
    read = len(found.visited) - found.reused
    runtime.output.info(
        ngettext(
            "{reused} unchanged folder taken from the index, {read} read.",
            "{reused} unchanged folders taken from the index, {read} read.",
            found.reused,
        ).format(reused=human_number(found.reused), read=human_number(read))
    )
    runtime.output.tip(
        _(
            "A photo changed in place by another program? 'audit --full' reads "
            "every folder (done anyway for those listed {days} days ago)."
        ).format(days=runtime.settings.scan.full_check_days)
    )


def tell_followed(runtime: Runtime, pruned: Pruned) -> None:
    """Say how many files moved or renamed since were recognised (TODO 0147).

    Args:
        runtime: Output.
        pruned: What the index did after the walk.
    """
    if not pruned.followed:
        return
    runtime.output.info(
        ngettext(
            "{count} file moved or renamed since the last audit: what the cache knew "
            "of it follows it.",
            "{count} files moved or renamed since the last audit: what the cache knew "
            "of them follows them.",
            pruned.followed,
        ).format(count=human_number(pruned.followed))
    )
