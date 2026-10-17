"""Serve the home page until Ctrl+C, or until the user chooses a step.

A step chosen ends the server with `100 + n`: the command exits with that code and
`mh` runs step `n` in the terminal, mounted as that command needs; only when `mh` set
`MEDIA_HYGIENE_LAUNCHER_STEPS`, else the page copies the command and keeps running.
The page only reads the tool folders: the photos stay mounted read-only.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.console.formatting import separators
from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.ending import (
    STOPPED,
    Ending,
    EndingDoor,
    serve_until_ended,
)
from media_hygiene.review.home_app import AUDIT_PATH, STEP_PATH, HomeApp
from media_hygiene.review.local_app import STATE_PATH
from media_hygiene.services.home_audit import HomeAudit
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from media_hygiene.services.reviewing import address_tip, page_url

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.console.page_progress import PageProgress
    from media_hygiene.review.home_views import HomeState
    from media_hygiene.services.home_audit import AuditResult
    from media_hygiene.services.runtime import Runtime

_PACKAGE: Final = "media_hygiene.review"
_TEMPLATE: Final = "home.html.j2"


def home_page(*, relays_steps: bool = False) -> bytes:
    """Render the home page; its content comes from `GET /api/state`.

    Args:
        relays_steps: The launcher runs a step chosen; else a button copies it.

    Returns:
        The page.
    """
    environment = translated_environment(_PACKAGE, escaped=("html", "j2"))
    template = environment.get_template(_TEMPLATE)
    return template.render(
        state_path=STATE_PATH,
        step_path=STEP_PATH,
        audit_path=AUDIT_PATH,
        relays_steps=relays_steps,
        thousands=separators()[0],
    ).encode()


def launcher_relays_steps() -> bool:
    """Tell whether `mh` runs the step a button chose (TODO 0210 sets the variable).

    Returns:
        True when `MEDIA_HYGIENE_LAUNCHER_STEPS` is set: ending the server with
        `100 + n` then runs step `n`; else the code would be lost.
    """
    return bool(os.environ.get(LAUNCHER_STEPS_VARIABLE))


@dataclass(frozen=True, slots=True)
class HomeSources:
    """Where the home page's content comes from: the tool folders, and its audit."""

    state: Callable[[], HomeState]
    audit: Callable[[PageProgress], AuditResult]


def serve_home(runtime: Runtime, sources: HomeSources, port: int) -> int:
    """Serve the home page until Ctrl+C or a step chosen; its audit stops then.

    Args:
        runtime: Settings, mount points and output.
        sources: Reads the tool folders, and runs the audit, for the page.
        port: The port to listen on, inside the container (0: any free one).

    Returns:
        `100 + n` for step `n` chosen; 0 on Ctrl+C or the page closed.
    """
    ending = Ending()
    audit = HomeAudit(sources.audit)
    reports_dir = runtime.locations.reports_dir
    relays = launcher_relays_steps()
    app = HomeApp(
        home_page(relays_steps=relays),
        sources.state,
        reports_dir,
        ending,
        audit,
        relays_steps=relays,
    )

    def ready(port: int) -> None:
        """Tell where the page is and how to open it from the host.

        Args:
            port: The port listened on, inside the container.
        """
        runtime.output.success(
            _("Home page ready, open {url} in your browser. Ctrl+C stops it.").format(
                url=page_url(port)
            )
        )
        address_tip(runtime.output, port)

    code = STOPPED
    try:
        with contextlib.suppress(KeyboardInterrupt):
            door = EndingDoor(app, ending)
            code = asyncio.run(serve_until_ended(door, port, ready))
    finally:
        audit.stop()  # between two files: the index keeps what it committed
    return code
