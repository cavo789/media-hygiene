"""Where the pages save the files set aside: `decisions.json` of the reports folder.

Shared by `search`, `browse` and `people`: one `chosen` key, one `clean --decisions`.
The reports folder is checked writable before each save, never trusted from the start.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.place import DEFAULT_DECISIONS, decisions_place
from media_hygiene.search.chosen import ChosenPlace, ChosenStore
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


def chosen_store(runtime: Runtime) -> ChosenStore:
    """The files set aside from the pages, in the reports folder.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The store of the `chosen` key.
    """
    reports = runtime.locations.reports_dir
    target = reports / DEFAULT_DECISIONS
    roots = runtime.mounts.data_roots(runtime.locations.data_dir)
    place = ChosenPlace(
        target,
        decisions_place(runtime.mapper, reports, target).host,
        runtime.mapper.roots_on_host(roots),
    )
    return ChosenStore(place, runtime.mapper)


def reports_ready(runtime: Runtime) -> None:
    """Check, before each save, that the reports folder keeps the decisions file.

    Args:
        runtime: Settings, mount points and output.

    Raises:
        MountError: It is not mounted, or not writable.
    """
    if not runtime.persistent(MountKind.REPORTS):
        raise MountError(
            _("The files set aside are saved in /reports: mount it, or they are lost.")
        )
    ensure_writable(runtime, MountKind.REPORTS)
