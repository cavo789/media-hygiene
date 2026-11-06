"""The scope of a classify run: target root, folders never moved, years, towns."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.engine import Scope
from media_hygiene.classify.late_files import refused_by_event
from media_hygiene.classify.whereabouts import load_towns
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.services.classify_inputs import mounted

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


def mounted_target(runtime: Runtime) -> Path | None:
    """`[classify] target`, in the container.

    Args:
        runtime: Settings, mount points.

    Returns:
        Its path; None without a target.

    Raises:
        MountError: The target is outside the mounted folders.
    """
    typed = runtime.settings.classify.target
    if not typed:
        return None
    target = runtime.mapper.to_container(typed)
    if not mounted(target, runtime.locations.data_dir):
        raise MountError(
            _("The target {path} is not mounted.").format(path=typed),
            _('Mount it under /data, e.g. -v "C:\\Photos triées:/data/c/Tri".'),
        )
    return target


def run_scope(runtime: Runtime, years: tuple[int, int] | None) -> Scope:
    """Target root, folders never moved, years.

    Args:
        runtime: Settings, mount points.
        years: The years asked for.

    Returns:
        The scope, in container paths.
    """
    settings, mapper = runtime.settings, runtime.mapper
    target = mounted_target(runtime)
    kept = (*settings.folders.untouched, *settings.classify.leave)
    return Scope(
        target,
        tuple(mapper.to_container(p) for p in kept),
        years,
        settings.keep.generic_folders,
        mapper.to_host,
        towns=load_towns(settings.classify),
        refused=refused_by_event(runtime.locations.config_dir, settings.classify.rules),
    )
