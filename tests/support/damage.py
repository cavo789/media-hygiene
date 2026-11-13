"""A small audited library and a byte flipped keeping size and date (0690, 0783)."""

from __future__ import annotations

import os
import shutil
from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.paths.mounts import MountTable
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from tests.support.runtime import make_runtime
from tests.support.scenes import scene

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime


def audit(runtime: Runtime) -> None:
    """An incremental audit."""
    AuditService(runtime, NullProgress()).run()


def damage_library(locations: Locations) -> tuple[Runtime, Path, Path]:
    """Two identical photos and one alone, audited; the runtime and the pair."""
    photos = locations.data_dir / "c" / "Photos"
    (photos / "a").mkdir(parents=True)
    (photos / "b").mkdir(parents=True)
    first = photos / "a" / "IMG_0001.jpg"
    scene(1).save(first, quality=90)
    twin = photos / "b" / "IMG_0001.jpg"
    shutil.copy2(first, twin)
    scene(2).save(photos / "a" / "IMG_0002.jpg", quality=90)
    runtime = replace(
        make_runtime(locations), mounts=MountTable(frozenset({photos}), (), ())
    )
    audit(runtime)
    return runtime, first, twin


def flip(path: Path, offset: int | None = None) -> None:
    """Flip one byte (the middle one by default), keeping size and modification time."""
    stat = path.stat()
    data = bytearray(path.read_bytes())
    data[len(data) // 2 if offset is None else offset] ^= 0xFF
    path.write_bytes(bytes(data))
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
