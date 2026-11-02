"""The summary of an audit of 2026-10-14, written in a runtime's reports folder."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.constants import RunKind

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class Found:
    """What the audit found."""

    copies: int = 0
    broken: int = 0
    backup_only: int = 0


def write_audit(runtime: Runtime, found: Found) -> None:
    """Write `20261014-100000-audit/summary.json`."""
    folder = runtime.locations.reports_dir / "20261014-100000-audit"
    folder.mkdir()
    summary = {
        "folder": folder.name,
        "kind": RunKind.AUDIT.value,
        "created_at": "2026-10-14T10:00:00+00:00",
        "files_scanned": 10,
        "duplicate_groups": found.copies,
        "duplicate_files": found.copies,
        "reclaimable_bytes": 100,
        "broken_files": found.broken,
        "backup_only": found.backup_only,
    }
    (folder / "summary.json").write_text(json.dumps(summary), "utf-8")
