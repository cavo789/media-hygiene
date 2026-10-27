r"""`media-hygiene push-step`: the container's part of `mh push` (0264).

Plumbing for `mh` only, hidden from `--help`, as `phone-plan` is. The steps, in order:
`plan` prints the plan's lines on stdout (`push_lines`); once the user agreed,
`start` reads them back on stdin and journals each rename `pending`; Windows renames
and copies; `prove` reads them back again, lists the target and journals what was
made. `undo` prints the renames of a run back, `undone` journals those made. Every
message goes to stderr; the photo folders and the target are mounted read-only.
"""

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli import folder_options
from media_hygiene.cli.cmd_push_flow import StepCall, run_step
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _
from media_hygiene.services.push_lines import PushStep


def push_step_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    step: Annotated[
        PushStep,
        typer.Argument(
            help=_("plan, start, prove, undo or undone."), show_default=False
        ),
    ],
    *,
    to: Annotated[
        str,
        typer.Option("--to", help=_("The backup folder."), show_default=False),
    ],
    run: Annotated[
        str,
        typer.Option(
            "--run", help=_("The run, for undo and undone."), show_default=False
        ),
    ] = "",
    anyway: Annotated[
        bool, typer.Option("--anyway", help=_("Past the safety stop."))
    ] = False,
    seconds: Annotated[
        float,
        typer.Option("--seconds", help=_("How long robocopy ran."), show_default=False),
    ] = 0.0,
    backup: Annotated[list[str] | None, folder_options.kept_backup()] = None,
) -> None:
    """Run one step of mh push in the container.

    Args:
        ctx: Typer context holding the runtime.
        step: The step.
        to: `--to`, the target.
        run: `--run`, the run to undo.
        anyway: `--anyway`, past the safety stop.
        seconds: `--seconds`, robocopy's time.
        backup: `--backup` folders, which the target must not overlap.
    """
    runtime = runtime_of(ctx).with_overrides(folder_options.backup_layer(backup))
    call = StepCall(to, run, anyway=anyway, seconds=seconds)
    with user_errors(runtime.output):
        run_step(runtime, step, call)
