"""`media-hygiene menu`: what `mh` alone shows, every step in order, the next one first.

The container cannot start the chosen step with the right mounts: `mh` does. So the
menu is printed on stderr and the selectable steps written on stdout, one
`number<TAB>command` per line (`0` for Enter); `mh` asks for the number, then runs
`mh <command>` itself, mounted exactly as a typed command. Run with `-t` instead
(`docker run -it … menu`), both streams are the screen: the menu is shown, the lines
for `mh` are not.
"""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

import typer

from media_hygiene.cli.context import runtime_of
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.status import Status
    from media_hygiene.services.update_check import UpdateNotice


def menu_command(ctx: typer.Context) -> None:
    """Show the steps of the three guides, then list the selectable ones for `mh`.

    Nothing is scanned: only the tool folders are read, as `status` does.

    Args:
        ctx: Typer context holding the runtime.
    """
    from media_hygiene.cli.menu_steps import build_menu, choice_lines
    from media_hygiene.cli.menu_view import show_menu
    from media_hygiene.cli.status_view import status_lines
    from media_hygiene.console.output import data_on_terminal
    from media_hygiene.services.next_command import LAUNCHER_VARIABLE

    runtime = runtime_of(ctx)
    output = runtime.output
    on_screen = data_on_terminal()
    output.console.quiet = False  # `-t`: the stderr console is muted for data
    # A large quarantine takes seconds to count through Docker Desktop: a spinner on
    # stderr (`mh` passes --color always) says the tool is alive (seen 2026-10-16).
    with output.console.status(_("Reading the tool folders…")):
        status, notice = _where(runtime)
    menu = build_menu(status, runtime.settings.clean.purge_hint_days)
    output.title(_("media-hygiene — where you are"))
    lines = status_lines(status)
    for line in (*lines[:2], *lines[-1:] * bool(status.missing)):
        output.info(line)
    output.blank()
    show_menu(runtime, menu, notice)
    if on_screen or not os.environ.get(LAUNCHER_VARIABLE):
        output.warning(
            _(
                "The menu runs its steps through mh: write it once with 'launcher' "
                "(step 0 of the guides), then type mh menu."
            )
        )
    if on_screen:
        return
    sys.stdout.write("".join(f"{line}\n" for line in choice_lines(menu)))
    sys.stdout.flush()


def _where(runtime: Runtime) -> tuple[Status, UpdateNotice | None]:
    """Read the tool folders, and whether a newer version is published.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        What the tool folders say; the newer version, Docker Hub asked once a day
        at most (0267).
    """
    from media_hygiene.services.status import read_status
    from media_hygiene.services.update_check import newer_version

    return read_status(runtime), newer_version(runtime)
