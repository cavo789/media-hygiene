"""The runs on the home page: the one still undoable, the quarantine, a new version."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.run_stamps import run_started
from media_hygiene.cli.status_view import ago, when
from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _
from media_hygiene.review.home_parts import HomeQuarantine, HomeUndo, HomeUpdate
from media_hygiene.services.launcher_host import UPDATE
from media_hygiene.services.next_command import LAUNCHER_FUNCTION
from media_hygiene.services.update_check import newer_version

if TYPE_CHECKING:
    from media_hygiene.cli.menu_steps import Menu
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.status import Status


def number_of(menu: Menu, name: str) -> int | None:
    """The number `mh menu` gives an action.

    Args:
        menu: The menu.
        name: The action.

    Returns:
        Its number; None when it cannot run now.
    """
    return next((line.number for line in menu.steps if line.step.name == name), None)


def home_undo(status: Status, menu: Menu) -> HomeUndo | None:
    """The newest run still undoable, and the command undoing it.

    Args:
        status: What the tool folders say.
        menu: The menu, numbering the step.

    Returns:
        It; None without such a run.
    """
    if not status.undoable:
        return None
    run = status.undoable[0]
    return HomeUndo(
        run_id=run.run_id,
        text=_("{kind} of {when}").format(
            kind=run.kind.value, when=when(run_started(run.run_id))
        ),
        command=f"{LAUNCHER_FUNCTION} undo {run.run_id}",
        number=number_of(menu, "undo"),
    )


def home_quarantine(status: Status) -> tuple[HomeQuarantine, ...]:
    """The quarantine, run by run.

    Args:
        status: What the tool folders say.

    Returns:
        One row per run still holding files, newest first.
    """
    return tuple(
        HomeQuarantine(
            run_id=run.run_id,
            files=human_number(run.files),
            size=human_size(run.size),
            since=ago(run.started),
        )
        for run in status.quarantine.runs
    )


def home_update(runtime: Runtime, menu: Menu) -> HomeUpdate | None:
    """The banner of a newer version, its button the step `mh update` (0267).

    Args:
        runtime: Settings and mount points.
        menu: The menu, numbering the step.

    Returns:
        It; None when no newer version is known.
    """
    notice = newer_version(runtime)
    if notice is None:
        return None
    return HomeUpdate(
        version=notice.version,
        notes=notice.notes,
        number=number_of(menu, UPDATE),
        command=f"{LAUNCHER_FUNCTION} {UPDATE}",
    )
