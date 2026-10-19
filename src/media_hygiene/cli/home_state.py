"""What the home page shows, from the same sources as `status` and `mh menu`.

The lines are those of `status`, the steps those of the menu, numbered alike: the
number a button sends is the one `mh` runs. The reports and their previews are read
from the reports folder; nothing else is read, nothing is scanned.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.home_reports import audit_previews, latest_reports
from media_hygiene.cli.menu_steps import build_menu
from media_hygiene.cli.menu_view import section_titles
from media_hygiene.cli.status_step import next_step
from media_hygiene.cli.status_view import status_lines
from media_hygiene.constants import (
    REPORT_INDEX_FILE_NAME,
)
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.home_views import (
    REPORTS_PREFIX,
    HomeNext,
    HomeSection,
    HomeState,
    HomeStep,
)
from media_hygiene.services.next_command import (
    LAUNCHER_FUNCTION,
    LAUNCHER_PHOTOS_VARIABLE,
)
from media_hygiene.services.status import read_status

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.cli.menu_steps import Menu, MenuStep
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.status import Status


_AI: Final = "🤖"
# Between two folders of LAUNCHER_PHOTOS_VARIABLE: no Windows name holds it (mh.ps1).
_SEPARATOR: Final = "|"


def home_state(runtime: Runtime) -> HomeState:
    """Read the tool folders, as `status` and `mh menu` do, into the home page's state.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The state.
    """
    status = read_status(runtime)
    purge_days = runtime.settings.clean.purge_hint_days
    menu = build_menu(status, purge_days)
    step = next_step(status, purge_days)
    proposed = menu.proposed
    reports = _reports_dir(runtime)
    return HomeState(
        lines=status_lines(status),
        given=_given(),
        sections=_sections(runtime, menu),
        proposed=HomeNext(
            number=proposed.number,
            command=f"{LAUNCHER_FUNCTION} {proposed.command}",
            why=step.text,
        )
        if proposed is not None and proposed.number and step is not None
        else None,
        undo=_undo(status),
        reports=latest_reports(reports) if reports else (),
        index=f"{REPORTS_PREFIX}{REPORT_INDEX_FILE_NAME}"
        if reports and (reports / REPORT_INDEX_FILE_NAME).is_file()
        else None,
        previews=audit_previews(reports) if reports else (),
    )


def _sections(runtime: Runtime, menu: Menu) -> tuple[HomeSection, ...]:
    """The guides and their steps, as the menu lists them.

    Args:
        runtime: Settings: whether a local model is set.
        menu: The menu.

    Returns:
        One section per guide, in order.
    """
    titles = section_titles()
    sections: dict[str, list[HomeStep]] = {}
    for line in menu.steps:
        sections.setdefault(titles[line.section], []).append(_step(runtime, line))
    return tuple(
        HomeSection(title=title, steps=tuple(steps))
        for title, steps in sections.items()
    )


def _step(runtime: Runtime, line: MenuStep) -> HomeStep:
    """One step, with the command, text and badges of the menu.

    Args:
        runtime: Settings: whether a local model is set.
        line: The step of the menu.

    Returns:
        The step for the page.
    """
    step = line.step
    text = step.text
    if not line.command and not step.typed:
        text += " " + _("(nothing to do yet)")
    badges = [step.risk.value]
    if step.ai and runtime.settings.classify.ai.model:
        badges.append(_AI)
    if step.optional:
        badges.append(_("optional"))
    shown = line.command or step.typed or step.command
    return HomeStep(
        number=line.number,
        command=f"{LAUNCHER_FUNCTION} {shown}",
        text=text,
        badges=tuple(badges),
        done=line.done,
        proposed=line.proposed,
        typed=bool(step.typed),
    )


def _undo(status: Status) -> str | None:
    """The undo line of the newest run still undoable.

    Args:
        status: What the tool folders say.

    Returns:
        The line, its command included; None without such a run.
    """
    if not status.undoable:
        return None
    run_id = status.undoable[0].run_id
    text = _("'undo {run_id}' still restores the files of the last run:")
    return f"{text.format(run_id=run_id)} {LAUNCHER_FUNCTION} undo {run_id}"


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
