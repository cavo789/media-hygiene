"""The scope of a classify run: target root, folders never moved, years, towns."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.engine import Scope
from media_hygiene.classify.whereabouts import load_towns
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.services.classify_inputs import mounted

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


def run_scope(runtime: Runtime, years: tuple[int, int] | None) -> Scope:
    """Target root, folders never moved, years.

    Args:
        runtime: Settings, mount points.
        years: The years asked for.

    Returns:
        The scope, in container paths.

    Raises:
        MountError: The target is outside the mounted folders.
    """
    settings, mapper = runtime.settings, runtime.mapper
    target = None
    if settings.classify.target:
        target = mapper.to_container(settings.classify.target)
        if not mounted(target, runtime.locations.data_dir):
            raise MountError(
                _("The target {path} is not mounted.").format(
                    path=settings.classify.target
                ),
                _('Mount it under /data, e.g. -v "C:\\Photos triées:/data/c/Tri".'),
            )
    kept = (*settings.folders.untouched, *settings.classify.leave)
    return Scope(
        target,
        tuple(mapper.to_container(p) for p in kept),
        years,
        settings.keep.generic_folders,
        mapper.to_host,
        towns=load_towns(settings.classify),
    )
