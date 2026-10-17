"""The setup tips closing an audit: the cache volume, the user's time zone."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.config import zone
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


def setup_tips(runtime: Runtime) -> None:
    """Suggest the settings worth adding once: the cache, the user's time zone.

    Args:
        runtime: Settings, mount points and output.
    """
    if not runtime.persistent(MountKind.CACHE):
        runtime.output.setting(
            _("-v media-hygiene-cache:/cache (much faster next audits)")
        )
    if zone.timezone_unknown():
        runtime.output.setting(_timezone_tip(runtime))


def _timezone_tip(runtime: Runtime) -> str:
    """Say how to give the tool the user's time zone, in config.toml when mounted.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The setting, as a fragment of the setup line.
    """
    if runtime.persistent(MountKind.CONFIG):
        return _(
            'timezone = "Europe/Brussels" in section [general] of {path} (times '
            "in your time zone, not UTC)"
        ).format(path=runtime.mapper.to_host(runtime.locations.config_file))
    return _("-e TZ=Europe/Brussels (times in your time zone, not UTC)")
