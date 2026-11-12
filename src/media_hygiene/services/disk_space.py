"""What the disk space page shows and changes: previews, quarantine, limits (0539).

Always read from the disk: the sizes each time, the limits from `config.toml` after
they are written with `toml_edit` (comments kept, atomic). Emptying the previews loses
nothing (they are made again when shown); *Purge*: `disk_purge`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.cli.status_view import ago, days_since
from media_hygiene.config.cache_settings import CacheSettings
from media_hygiene.config.clean_settings import CleanSettings
from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.places.toml_edit import (
    document_of,
    loaded,
    table_of,
    write_document,
)
from media_hygiene.report.preview_cache import trim_previews
from media_hygiene.services.disk_only import only_by_run
from media_hygiene.services.disk_purge import PurgeReadBack
from media_hygiene.services.status import read_status

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

_CACHE: Final = "cache"
_CLEAN: Final = "clean"
_MAX_GB: Final = "previews_max_gb"
_DAYS: Final = "purge_hint_days"


class Limits(BaseModel):
    """The two limits, as the page sends them and the file holds them."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    previews_max_gb: float = Field(gt=0)
    purge_hint_days: int = Field(ge=1)


class DiskRun(BaseModel):
    """The quarantine of one run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str
    files: str
    count: int  # the same, to compare with the tiles shown (0616)
    size: str
    since: str
    old: bool
    only: str = ""  # its files that exist nowhere else (0775); empty: not known


class DiskState(BaseModel):
    """Everything the page draws."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    previews_size: str
    previews_empty: bool
    quarantine_size: str
    quarantine_only: str = ""  # files that exist nowhere else, in all; empty: not known
    runs: tuple[DiskRun, ...]
    limits: Limits
    purged: PurgeReadBack | None = None  # the last purge asked here, read back (0616)


def previews_bytes(folder: Path | None) -> int:
    """The room the previews take.

    Args:
        folder: The cache folder of previews, or None.

    Returns:
        Bytes; 0 when missing.
    """
    if folder is None or not folder.is_dir():
        return 0
    return sum(path.stat().st_size for path in folder.iterdir() if path.is_file())


def limits_of(config_file: Path) -> Limits:
    """The limits the file holds, read from the disk.

    Args:
        config_file: `config.toml`.

    Returns:
        They, each default when not written.
    """
    tables = loaded(config_file)
    cache = CacheSettings.model_validate(tables.get(_CACHE, {}))
    clean = CleanSettings.model_validate(tables.get(_CLEAN, {}))
    return Limits(
        previews_max_gb=cache.previews_max_gb, purge_hint_days=clean.purge_hint_days
    )


def save_limits(config_file: Path, limits: Limits) -> Limits:
    """Write the limits, then read them back.

    Args:
        config_file: `config.toml`.
        limits: What the page sent.

    Returns:
        What the file now holds.
    """
    document = document_of(config_file)
    table_of(document, _CACHE)[_MAX_GB] = limits.previews_max_gb
    table_of(document, _CLEAN)[_DAYS] = limits.purge_hint_days
    write_document(config_file, document)
    return limits_of(config_file)


def empty_previews(runtime: Runtime) -> None:
    """Remove every preview kept: made again when next shown.

    Args:
        runtime: Mount points.
    """
    trim_previews(runtime.previews_dir, 0)


def disk_state(runtime: Runtime) -> DiskState:
    """Read the sizes and the limits from the disk.

    Args:
        runtime: Settings and mount points.

    Returns:
        The state.
    """
    limits = limits_of(runtime.locations.config_file)
    quarantine = read_status(runtime).quarantine
    size = previews_bytes(runtime.previews_dir)
    counted = only_by_run(runtime, [run.run_id for run in quarantine.runs])
    only = (
        {}
        if counted is None
        else {r.run_id: counted.get(r.run_id, r.files) for r in quarantine.runs}
    )
    runs = tuple(
        DiskRun(
            run_id=run.run_id,
            files=human_number(run.files),
            count=run.files,
            size=human_size(run.size),
            since=ago(run.started),
            old=days_since(run.started) >= limits.purge_hint_days,
            only=human_number(only[run.run_id]) if run.run_id in only else "",
        )
        for run in quarantine.runs
    )
    return DiskState(
        previews_size=human_size(size),
        previews_empty=size == 0,
        quarantine_size=human_size(quarantine.size),
        quarantine_only=human_number(sum(only.values())) if only else "",
        runs=runs,
        limits=limits,
    )
