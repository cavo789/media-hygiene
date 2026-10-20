"""Whether a folder a run created can be removed by `undo`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from pathlib import Path


def folder_blocker(folder: Path) -> str | None:
    """Tell why a folder a run created cannot be removed.

    Args:
        folder: The folder.

    Returns:
        The reason, or None when it is there and empty.
    """
    if not folder.is_dir():
        return _("the folder is gone already")
    return _("the folder is not empty") if any(folder.iterdir()) else None
