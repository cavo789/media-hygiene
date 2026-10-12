"""Ctrl+C ends any command with one calm line, never a traceback."""

from __future__ import annotations

from typing import TYPE_CHECKING, NoReturn

import typer

from media_hygiene.cli.safety import READ_ONLY_COMMANDS
from media_hygiene.console.output import Output, make_console
from media_hygiene.constants import ColorMode, ExitCode
from media_hygiene.i18n import _
from media_hygiene.services.runtime import Runtime

if TYPE_CHECKING:
    from typer._click import Context


def stop_on_interrupt(ctx: Context) -> NoReturn:
    """Say that the command stopped, and whether the photos were left untouched.

    Args:
        ctx: Context of the root group, holding the runtime once it is built.

    Raises:
        typer.Exit: Always, with the conventional code of an interrupted program.
    """
    runtime = ctx.obj
    output = (
        runtime.output
        if isinstance(runtime, Runtime)
        else Output(make_console(ColorMode.AUTO))
    )
    output.blank()
    if ctx.invoked_subcommand in READ_ONLY_COMMANDS:
        output.warning(_("Stopped (Ctrl+C). Your photos and videos were not touched."))
    else:
        output.warning(_("Stopped (Ctrl+C)."))
    raise typer.Exit(ExitCode.INTERRUPTED)
