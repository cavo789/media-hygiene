"""The damaged files' page (0783): each beside its good copy, *Restore* per file.

The page lists what `clean --repair` would list (`good_copy.repairables`: every copy
proven by reading it in full now). *Restore* proves the copies again at that moment: a
copy gone or changed meanwhile refuses its file and nothing of it is moved. The others
are restored under one journaled run (`repair`), each read back from the disk; the
damaged file waits in the quarantine, `undo` of the run puts it back.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.constants import VIDEO_EXTENSIONS
from media_hygiene.i18n import _
from media_hygiene.review.near_views import folder_and_name
from media_hygiene.review.views import ORIGINAL_LINK, PREVIEW_LINK
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.good_copy import CopyPlace, repairables
from media_hygiene.services.repair import jobs_of, repair

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.services.good_copy import Repairable
    from media_hygiene.services.runtime import Runtime

_FROZEN: Final = ConfigDict(frozen=True, extra="forbid")
COPY_SUFFIX: Final = "~copy"  # a key's good copy: `<key>~copy`
_KEY_LENGTH: Final = 20


class DamagedTile(BaseModel):
    """One damaged file, as the page shows it."""

    model_config = _FROZEN

    key: str
    name: str
    folder: str  # as Windows names it
    since: str  # the day it was found changed
    good: str  # the last day it read fine
    good_copy: str | None  # its good copy, as Windows names it; None: none here
    in_quarantine: bool
    video: bool
    preview: str
    original: str
    copy_preview: str | None


class RepairState(BaseModel):
    """`GET /api/state`: every damaged file."""

    model_config = _FROZEN

    tiles: tuple[DamagedTile, ...]


class Repaired(BaseModel):
    """`POST /api/restore`: what was restored, read back, and what was refused."""

    model_config = _FROZEN

    back: tuple[str, ...]  # the host paths read back holding the good content
    left: tuple[str, ...]  # "<path>: <reason>"
    run_id: str | None  # the run to undo; None: nothing moved
    state: RepairState


def tile_key(path: str) -> str:
    """The key of a damaged file: a digest of its path (no path in a URL).

    Args:
        path: The file, inside the container.

    Returns:
        The key.
    """
    return hashlib.sha256(path.encode()).hexdigest()[:_KEY_LENGTH]


def _tile(runtime: Runtime, item: Repairable) -> DamagedTile:
    row = item.damaged
    key = tile_key(row.path)
    folder, name = folder_and_name(str(runtime.mapper.to_host(Path(row.path))))
    suffix = Path(row.path).suffix.lower()
    copy = None if item.copy is None else str(runtime.mapper.to_host(item.copy))
    return DamagedTile(
        key=key,
        name=name,
        folder=folder,
        since=row.damaged_since[:10],
        good=row.verified_at[:10],
        good_copy=copy,
        in_quarantine=item.place is CopyPlace.QUARANTINE,
        video=suffix in VIDEO_EXTENSIONS,
        preview=f"{PREVIEW_LINK}{key}.jpg",
        original=f"{ORIGINAL_LINK}{key}{suffix}",
        copy_preview=None if copy is None else f"{PREVIEW_LINK}{key}{COPY_SUFFIX}.jpg",
    )


def repair_state(runtime: Runtime) -> RepairState:
    """Every damaged file of the index, its copy proven now.

    Args:
        runtime: Settings and mount points.

    Returns:
        Its tiles, by path.
    """
    return RepairState(
        tiles=tuple(_tile(runtime, item) for item in repairables(runtime))
    )


def source_of(runtime: Runtime, key: str) -> Path | None:
    """The file a tile shows: the damaged one, or its good copy (`~copy`).

    Args:
        runtime: Settings and mount points.
        key: The tile's key.

    Returns:
        The file, or None for an unknown key.
    """
    base = key.removesuffix(COPY_SUFFIX)
    for item in repairables(runtime):
        if tile_key(item.damaged.path) == base:
            return item.copy if key != base else Path(item.damaged.path)
    return None


def restore_damaged(runtime: Runtime, keys: Iterable[str]) -> Repaired:
    """Restore the files picked from their good copy, proven again now.

    Args:
        runtime: Settings, mount points and output.
        keys: The tiles picked; an unknown key is ignored.

    Returns:
        The files read back, the others with their reason, the run, the page again.

    Raises:
        MountError: No persistent journal, or read-only photo folders; nothing moved.
    """
    wanted = set(keys)
    picked = [
        item for item in repairables(runtime) if tile_key(item.damaged.path) in wanted
    ]
    host = runtime.mapper.to_host
    left = [
        _("{path}: its good copy is gone or changed: nothing was moved.").format(
            path=host(Path(item.damaged.path))
        )
        for item in picked
        if item.copy is None
    ]
    jobs = jobs_of(picked)
    if not jobs:
        return Repaired(
            back=(), left=tuple(left), run_id=None, state=repair_state(runtime)
        )
    result = repair(runtime, jobs, NullProgress())
    back = tuple(str(host(path)) for path in result.proven)
    left += [
        f"{host(incident.path)}: {incident.reason}"
        for incident in (*result.outcome.skipped, *result.outcome.failed)
    ]
    return Repaired(
        back=back, left=tuple(left), run_id=result.run_id, state=repair_state(runtime)
    )
