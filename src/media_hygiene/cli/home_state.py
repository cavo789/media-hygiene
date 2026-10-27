"""What the home page shows, from the same sources as `status` and `mh menu`.

The actions are those of the menu, numbered alike: the number a button sends is the
one `mh` runs. The reports and their previews are read from the reports folder;
nothing else is read, nothing is scanned.
"""

from __future__ import annotations

import os
from importlib.metadata import version
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.home_actions import home_actions, home_next
from media_hygiene.cli.home_cycle import CycleFacts, home_spaces
from media_hygiene.cli.home_findings import home_findings
from media_hygiene.cli.home_folders import home_folders
from media_hygiene.cli.home_reports import audit_previews, latest_reports
from media_hygiene.cli.home_runs import home_quarantine, home_undo, home_update
from media_hygiene.cli.home_tiles import home_tiles
from media_hygiene.cli.menu_entry import Doc
from media_hygiene.cli.menu_steps import build_menu, full_catalog
from media_hygiene.cli.status_step import next_step
from media_hygiene.cli.status_view import status_lines
from media_hygiene.constants import APP_NAME, REPORT_INDEX_FILE_NAME, Locale
from media_hygiene.docs.served import served_index, served_url
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.home_parts import HomeLink
from media_hygiene.review.home_views import REPORTS_PREFIX, HomeState
from media_hygiene.services.launcher_host import windows_menu
from media_hygiene.services.launcher_stamp import say_stamp
from media_hygiene.services.next_command import LAUNCHER_PHOTOS_VARIABLE
from media_hygiene.services.status import read_status

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


# Between two folders of LAUNCHER_PHOTOS_VARIABLE: no Windows name holds it (mh.ps1).
_SEPARATOR: Final = "|"
_DOCS_HOME: Final = Doc("")  # the documentation's home


def home_state(runtime: Runtime) -> HomeState:
    """Read the tool folders, as `status` and `mh menu` do, into the home page's state.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The state.
    """
    status = read_status(runtime)
    purge_days = runtime.settings.clean.purge_hint_days
    windows = windows_menu()
    menu = build_menu(status, purge_days, windows=windows)
    areas = full_catalog().areas
    update = home_update(runtime, menu)
    reports = _reports_dir(runtime)
    return HomeState(
        version=version(APP_NAME),
        lines=status_lines(status),
        spaces=home_spaces(areas, CycleFacts(status, menu, newer=update is not None)),
        actions=home_actions(menu),
        docs=HomeLink(
            url=served_url(_DOCS_HOME), url_en=served_url(_DOCS_HOME, Locale.EN)
        ),
        docs_index=served_index(),
        given=_given(),
        proposed=home_next(menu, next_step(status, purge_days), areas),
        tiles=home_tiles(status),
        findings=home_findings(status, backups=bool(runtime.settings.folders.backups)),
        folders=home_folders(runtime),
        quarantine=home_quarantine(status),
        undo=home_undo(status, menu),
        reports=latest_reports(reports) if reports else (),
        index=f"{REPORTS_PREFIX}{REPORT_INDEX_FILE_NAME}"
        if reports and (reports / REPORT_INDEX_FILE_NAME).is_file()
        else None,
        previews=audit_previews(reports) if reports else (),
        update=update,
        stale=say_stamp(),
        windows=windows,
        ai=bool(runtime.settings.classify.ai.model),
    )


def _reports_dir(runtime: Runtime) -> Path | None:
    """The reports folder, when it is mounted.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        It, or None.
    """
    reports = runtime.locations.reports_dir
    mounted = runtime.persistent(MountKind.REPORTS) and reports.is_dir()
    return reports if mounted else None


def _given() -> tuple[str, ...]:
    """The folders `mh` gave this page with --photos, a right-click's (TODO 0258).

    Returns:
        One line per folder; none when `mh` gave none.
    """
    folders = os.environ.get(LAUNCHER_PHOTOS_VARIABLE, "").split(_SEPARATOR)
    text = _("This page also analyses: {folder}")
    return tuple(text.format(folder=folder) for folder in folders if folder)
