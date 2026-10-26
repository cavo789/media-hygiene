"""An unexpected error ends a command with a few calm lines, never a traceback.

A domain error (`MediaHygieneError`) already says what to do; anything else is a bug.
The user reads what failed, whether the photos were touched, and how to report it.
`MEDIA_HYGIENE_DEBUG=1`, never set in the image, lets the traceback through for the
developer.
"""

from __future__ import annotations

import os
import shlex
import sys
from importlib.metadata import version
from typing import TYPE_CHECKING, Final, NoReturn

import typer
from rich.markup import escape

from media_hygiene.cli.interrupted import output_of, untouched
from media_hygiene.cli.safety import GO_PAGES, READ_ONLY_COMMANDS
from media_hygiene.constants import APP_NAME, HOME_PAGE, ExitCode
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from typer._click import Context

DEBUG_VARIABLE: Final = "MEDIA_HYGIENE_DEBUG"
ISSUES: Final = f"{HOME_PAGE}/issues"
# The commands whose changes the journal holds: `undo` puts them back.
UNDOABLE: Final = frozenset({"clean", "sort"} | GO_PAGES)
_DISTRIBUTION: Final = "media-hygiene"


def debugging() -> bool:
    """Tell whether the developer asked for the traceback.

    Returns:
        True when `MEDIA_HYGIENE_DEBUG` is set to a non-empty value other than 0.
    """
    return os.environ.get(DEBUG_VARIABLE, "") not in {"", "0"}


def stop_on_error(ctx: Context, error: Exception) -> NoReturn:
    """Say what failed, whether the photos were touched, and how to report it.

    Args:
        ctx: Context of the root group.
        error: The unexpected exception.

    Raises:
        typer.Exit: Always, with the failure code.
    """
    output = output_of(ctx)
    command = ctx.invoked_subcommand or APP_NAME
    output.blank()
    line = _("Unexpected error during {command}: {kind}: {message}")
    kind, message = type(error).__name__, str(error)
    output.error(escape(line.format(command=command, kind=kind, message=message)))
    if command in READ_ONLY_COMMANDS:
        output.info(untouched())
    elif command in UNDOABLE:
        output.info(_("What was already done is in the journal: 'undo' puts it back."))
    tip = _(
        "Please report it at {url}, with the version ({version}), the command typed "
        "({typed}) and this message. -e {variable}=1 shows the details."
    )
    typed = shlex.join([APP_NAME, *sys.argv[1:]])
    found = {"url": ISSUES, "version": version(_DISTRIBUTION), "typed": typed}
    output.tip(escape(tip.format(variable=DEBUG_VARIABLE, **found)))
    raise typer.Exit(ExitCode.FAILURE) from error
