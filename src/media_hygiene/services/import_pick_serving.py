"""Serve the page of `import --pick`: typed, or under the home server (0590, 0594)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.i18n.live import PerLocale
from media_hygiene.review.import_pick_app import COPY_PATH, LEAVE_PATH, ImportPickApp
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.import_pick import ImportDesk
from media_hygiene.services.import_run import ImportService
from media_hygiene.services.pick_page_serving import pick_page, serve_pick_page

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.services.import_plan import ImportPlan
    from media_hygiene.services.runtime import Runtime

PAGE_TEMPLATE: Final = "import_pick.html.j2"


def import_page() -> bytes:
    """Render the page; its paths relative to it.

    Returns:
        The page, in the language in use.
    """
    paths = {"leave_path": LEAVE_PATH, "copy_path": COPY_PATH}
    return pick_page(PAGE_TEMPLATE, paths)


def planned_app(runtime: Runtime, executor: Executor) -> ImportPickApp:
    """The page's app on the home server: checks, audit from the index, plan.

    Args:
        runtime: Settings, mount points and output.
        executor: The worker pool.

    Returns:
        The app.
    """
    service = ImportService(runtime, NullProgress())
    service.ensure_ready()
    desk = ImportDesk(runtime, service.prepare())
    return ImportPickApp(runtime, desk, PerLocale(import_page), executor)


def serve_import_pick(runtime: Runtime, plan: ImportPlan, port: int) -> int:
    """Serve the page of a plan already made in the console.

    Args:
        runtime: Settings, mount points and output.
        plan: The copies.
        port: The port to listen on, inside the container.

    Returns:
        The exit code the page ended on (0: Ctrl+C).
    """
    said = _(
        "The files only this folder holds are ready, open {url} in your browser. "
        "Nothing is copied before the page's button. Ctrl+C stops the page."
    )

    def app_of(executor: Executor) -> ImportPickApp:
        """Build the app.

        Args:
            executor: The worker pool.

        Returns:
            The app.
        """
        desk = ImportDesk(runtime, plan)
        return ImportPickApp(runtime, desk, PerLocale(import_page), executor)

    return serve_pick_page(runtime, app_of, (port, said))
