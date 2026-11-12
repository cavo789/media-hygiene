"""Where the names of the people go: `config.toml`, when it can be written."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import is_writable

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


def names_file(runtime: Runtime) -> Path | None:
    """The `config.toml` the names go to; None when it cannot be written.

    Args:
        runtime: Mount points.

    Returns:
        The file, or None.
    """
    config = runtime.locations.config_file
    if runtime.persistent(MountKind.CONFIG) and is_writable(config.parent):
        return config
    return None
