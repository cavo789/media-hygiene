"""Serve the page of `undo --pick` (0525): typed, or by the home server (0591)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.i18n.live import PerLocale
from media_hygiene.review.quarantine_app import RESTORE_PATH, QuarantineApp
from media_hygiene.review.served_more import DISK_PURGE_PATH
from media_hygiene.services.pick_page_serving import pick_page, serve_pick_page

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.services.runtime import Runtime

PAGE_TEMPLATE: Final = "quarantine.html.j2"


def quarantine_page() -> bytes:
    """Render the page; its paths relative to it.

    Returns:
        The page, in the language in use.
    """
    return pick_page(
        PAGE_TEMPLATE, {"restore_path": RESTORE_PATH, "purge_path": DISK_PURGE_PATH}
    )


def serve_quarantine(runtime: Runtime, port: int) -> int:
    """Serve the quarantine's page; each *Restore* acts at once, journaled.

    Args:
        runtime: Settings, mount points and output.
        port: The port to listen on, inside the container (0: any free one).

    Returns:
        The exit code the page ended on (0: Ctrl+C).
    """
    said = _(
        "The quarantine is ready, open {url} in your browser. Each photo "
        "restored goes back at once, journaled. Ctrl+C stops the page."
    )

    def app_of(executor: Executor) -> QuarantineApp:
        """Build the app.

        Args:
            executor: The worker pool.

        Returns:
            The app.
        """
        return QuarantineApp(runtime, PerLocale(quarantine_page), executor)

    return serve_pick_page(runtime, app_of, (port, said))
