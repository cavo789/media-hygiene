"""The home page's step that applies the decisions, for *Apply now* (0243, 0288).

`browse`, `review` and `review --near` offer it when `mh`'s home loop opened them.

Read from the same sources as `mh menu` and the home page, so the number the page
ends with is the one `mh` runs: `clean --decisions` (with `--tier near` when near
duplicates were reviewed), as `status` proposes it.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

import typer

from media_hygiene.cli.menu_steps import build_menu
from media_hygiene.cli.status_step import Slot
from media_hygiene.i18n import _
from media_hygiene.review.apply_api import ApplyStep
from media_hygiene.services.home import launcher_relays_steps
from media_hygiene.services.next_command import LAUNCHER_FUNCTION
from media_hygiene.services.status import read_status

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.services.runtime import Runtime


def apply_step(runtime: Runtime) -> ApplyStep | None:
    """The numbered step of the menu that applies the decisions, read now.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        Its number and full command; None when the menu has none to select.
    """
    menu = build_menu(read_status(runtime), runtime.settings.clean.purge_hint_days)
    return next(
        (
            ApplyStep(line.number, f"{LAUNCHER_FUNCTION} {line.command}")
            for line in menu.steps
            if line.step.slot is Slot.APPLY and line.number
        ),
        None,
    )


def page_apply(runtime: Runtime) -> Callable[[], ApplyStep | None] | None:
    """The step a page's *Apply now* ends on, read when clicked.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        It, when `mh`'s home loop opened the page and runs the step chosen; None:
        no button.
    """
    return partial(apply_step, runtime) if launcher_relays_steps() else None


def end_on_applied(runtime: Runtime, code: int) -> None:
    """Say the step *Apply now* chose, then end with its code for `mh` to run it.

    Args:
        runtime: Settings, mount points and output.
        code: The exit code the page ended with; 0: no step chosen.

    Raises:
        Exit: With `STEP_EXIT_BASE + n` when *Apply now* chose step `n`.
    """
    step = apply_step(runtime) if code else None
    if step is None:
        return
    said = _("Apply now, chosen on the page: {command}")
    runtime.output.info(said.format(command=step.command))
    raise typer.Exit(code)
