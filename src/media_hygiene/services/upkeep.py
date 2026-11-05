"""`media-hygiene upkeep`: the steps of `[routine]`, one command after the other (0519).

Each step is the real command in its own process, its questions and its output in the
same window: `clean` and `purge` keep their confirmation. A step that fails stops the
chain, what came before stays done.
"""

from __future__ import annotations

import subprocess  # this tool's own command, its arguments built here
import sys
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.status_view import days_since
from media_hygiene.config.routine_settings import RoutineStep
from media_hygiene.i18n import _
from media_hygiene.services.status import read_status

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from media_hygiene.services.runtime import Runtime

type StepRunner = Callable[[Sequence[str]], int]

_SIMPLE: Final = {
    RoutineStep.AUDIT: ("audit",),
    RoutineStep.COPIES: ("clean",),
    RoutineStep.REPORTS: ("reports",),
}


def run_command(arguments: Sequence[str]) -> int:
    """Run this tool's command in the same window.

    Args:
        arguments: Its words.

    Returns:
        Its exit code.
    """
    command = (sys.executable, "-m", "media_hygiene", *arguments)
    return subprocess.run(command, check=False).returncode  # noqa: S603


def old_runs(runtime: Runtime) -> tuple[str, ...]:
    """The quarantine runs old enough to be worth purging, read from the disk.

    Args:
        runtime: Settings and mount points.

    Returns:
        Their identifiers.
    """
    days = runtime.settings.clean.purge_hint_days
    runs = read_status(runtime).quarantine.runs
    return tuple(run.run_id for run in runs if days_since(run.started) >= days)


def commands_of(runtime: Runtime, step: RoutineStep) -> tuple[tuple[str, ...], ...]:
    """The commands of a step.

    Args:
        runtime: Settings and mount points.
        step: The step.

    Returns:
        Each command's words; `purge` one per old run, maybe none.
    """
    if step is RoutineStep.PURGE:
        return tuple(("purge", run) for run in old_runs(runtime))
    return (_SIMPLE[step],)


def run_upkeep(runtime: Runtime, run: StepRunner = run_command) -> int:
    """Run the steps of `[routine]`, in order.

    Args:
        runtime: Settings, mount points and output.
        run: Runs one command.

    Returns:
        0, or the code of the step that stopped the chain.
    """
    steps = runtime.settings.routine.steps
    if not steps:
        runtime.output.info(_("Nothing to do: [routine] steps is empty."))
    for step in steps:
        runtime.output.title(_("Upkeep: {step}").format(step=step.value))
        for command in commands_of(runtime, step):
            code = run(command)
            if code:
                runtime.output.warning(
                    _(
                        "'{command}' stopped (code {code}): the next steps did not run."
                    ).format(command=" ".join(command), code=code)
                )
                return code
    return 0
