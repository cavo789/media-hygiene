"""What only a backup (a NAS) holds, minus what the user dealt with before (0245).

Three photos only on the NAS: one set aside before in a burst review (0216), one deleted
in the Explorer, waiting for `review --gone` (0224), one never seen in the library. Only
the last is to import; the other two are counted apart.
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING, Final

from media_hygiene.console.backup_view import push_lines
from media_hygiene.paths.host_paths import HostPathMapper
from tests.integration.test_returned_files import audit, set_burst_aside, shots
from tests.support.runtime import make_runtime
from tests.support.scenes import scene

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.layers import Layer
    from media_hygiene.paths.locations import Locations

_BACKUP: Final[Layer] = {"folders": {"backups": ["D:\\backup"]}}


def nas(locations: Locations) -> Path:
    """The backup folder, as `mh` mounts a NAS share."""
    folder = locations.data_dir / "d" / "backup"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def test_only_what_was_never_dealt_with_is_proposed(locations: Locations) -> None:
    """Set aside before, deleted in the Explorer: counted apart, never proposed."""
    runtime = make_runtime(locations, _BACKUP)
    kept, aside = shots(locations.data_dir)
    backup = nas(locations)
    nas_aside = backup / "2024" / aside.name
    nas_aside.parent.mkdir()
    shutil.copy2(aside, nas_aside)
    deleted = kept.parent / "IMG_0003.jpg"
    scene(3).save(deleted, quality=90)
    nas_deleted = backup / "2024" / deleted.name
    shutil.copy2(deleted, nas_deleted)
    fresh = backup / "2019" / "IMG_9999.jpg"
    fresh.parent.mkdir()
    scene(9).save(fresh, quality=90)

    set_burst_aside(runtime, kept, aside)  # audits too: the deleted one is indexed
    deleted.unlink()
    (coverage,) = audit(runtime).backups

    assert {file.path for file in coverage.only} == {nas_aside, nas_deleted, fresh}
    assert [file.path for file in coverage.to_import] == [fresh]
    assert coverage.dealt.set_aside == {nas_aside}
    assert coverage.dealt.deleted == {nas_deleted}
    _lacks, holds = push_lines(coverage, HostPathMapper(locations.data_dir))
    assert "1 file is only in it, never in your photos" in holds
    assert "2 other files are ones you set aside or deleted before" in holds


def test_without_a_backup_nothing_is_read_for_it(locations: Locations) -> None:
    """No backup folder: no recognition of deletions, the audit as before."""
    kept, _aside = shots(locations.data_dir)
    kept.unlink()
    assert not audit(make_runtime(locations)).backups
