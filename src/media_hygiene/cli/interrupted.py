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
    output = output_of(ctx)
    output.blank()
    if ctx.invoked_subcommand in READ_ONLY_COMMANDS:
        output.warning(f"{_('Stopped (Ctrl+C).')} {untouched()}")
    else:
        output.warning(_("Stopped (Ctrl+C)."))
    raise typer.Exit(ExitCode.INTERRUPTED)


def untouched() -> str:
    """The reassurance after a read-only command stopped, whatever stopped it.

    Returns:
        The translated sentence.
    """
    return _("Your photos and videos were not touched.")


def output_of(ctx: Context) -> Output:
    """Where to print once a command stopped: its own output, else a new one.

    Args:
        ctx: Context of the root group, holding the runtime once it is built.

    Returns:
        The output.
    """
    runtime = ctx.obj
    if isinstance(runtime, Runtime):
        return runtime.output
    return Output(make_console(ColorMode.AUTO))
