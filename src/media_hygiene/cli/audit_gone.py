"""After an audit run by `mh`: open `review --gone` at once, when the user says so.

The container cannot serve the page: `mh` publishes its port for page commands only.
So the audit ends with `ExitCode.GONE_REVIEW` and `mh` runs `review --gone` itself.
A plain `docker run`, or no terminal to answer in, keeps the next step line alone.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import typer

from media_hygiene.cli.audit_people import has_terminal
from media_hygiene.cli.next_steps import carried, suggest
from media_hygiene.constants import ExitCode
from media_hygiene.i18n import _
from media_hygiene.services.next_command import LAUNCHER_VARIABLE, NextVerb

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


def offer_gone_review(runtime: Runtime) -> None:
    """Ask whether to review the files gone now; `mh` opens the page on a yes.

    Args:
        runtime: Output.

    Raises:
        Exit: With `ExitCode.GONE_REVIEW`, for `mh` to open `review --gone`.
    """
    if not os.environ.get(LAUNCHER_VARIABLE) or not has_terminal():
        return
    if runtime.output.confirm(_("Open the review of the vanished files now?")):
        raise typer.Exit(ExitCode.GONE_REVIEW)


def gone_step(ctx: typer.Context, runtime: Runtime) -> None:
    """Nothing else to do: lead to the files deleted outside.

    Args:
        ctx: Typer context of the audit, whose options the next command keeps.
        runtime: Settings, mount points and output.
    """
    suggest(
        runtime,
        _(
            "say in 'review --gone' which vanished files you deleted on "
            "purpose: they will be set aside if they come back."
        ),
        NextVerb(
            carried(runtime, "review --gone", ctx), port=runtime.settings.review.port
        ),
    )
    offer_gone_review(runtime)
