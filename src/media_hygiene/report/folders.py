"""New report folders: `<stamp>-<suffix>`, never one that already exists."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from pathlib import Path

_STAMP_FORMAT: Final = "%Y%m%d-%H%M%S"


def new_report_folder(reports_dir: Path, suffix: str) -> Path:
    """Create `<stamp>-<suffix>`, with a number when two runs share a second.

    Args:
        reports_dir: The reports mount point.
        suffix: What the folder holds, e.g. `classify`.

    Returns:
        The new, empty folder.
    """
    base = f"{datetime.now(UTC).strftime(_STAMP_FORMAT)}-{suffix}"
    folder, number = reports_dir / base, 1
    while folder.exists():
        number += 1
        folder = reports_dir / f"{base}-{number}"
    folder.mkdir(parents=True)
    return folder
