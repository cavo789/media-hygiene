"""The one step `status` ends with, as a full command, and how to undo the last run."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.next_steps import carried, safety, suggest
from media_hygiene.cli.status_step import next_step
from media_hygiene.i18n import _
from media_hygiene.services.next_command import CHANGING, NextVerb

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.status import Status


def advise_status(runtime: Runtime, status: Status) -> None:
    """Add the undo line of the newest run, then the one step that comes next.

    Args:
        runtime: Settings, mount points and output.
        status: What the tool folders say.
    """
    if status.undoable:
        run_id = status.undoable[0].run_id
        safety(
            runtime,
            _("'undo {run_id}' still restores the files of the last run:").format(
                run_id=run_id
            ),
            NextVerb(carried(runtime, f"undo {run_id}"), CHANGING),
        )
    step = next_step(status, runtime.settings.clean.purge_hint_days)
    if step is None:
        runtime.output.success(_("Nothing left to do: everything is applied."))
        return
    command = carried(runtime, step.command)
    suggest(runtime, step.text, NextVerb(command, step.needs, step.port))
