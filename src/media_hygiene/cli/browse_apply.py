"""The home page's step that applies the decisions, for *Apply now* on `browse` (0243).

Read from the same sources as `mh menu` and the home page, so the number the page
ends with is the one `mh` runs: `clean --decisions` (with `--tier near` when near
duplicates were reviewed), as `status` proposes it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.menu_steps import build_menu
from media_hygiene.cli.status_step import Slot
from media_hygiene.search.apply_api import ApplyStep
from media_hygiene.services.next_command import LAUNCHER_FUNCTION
from media_hygiene.services.status import read_status

if TYPE_CHECKING:
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
