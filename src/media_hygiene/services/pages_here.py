"""The pages of tiles the home server serves under their prefix (0591, 0590, 0594)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.review.quarantine_app import QuarantineApp
from media_hygiene.review.served_more import IMPORT_PAGE, QUARANTINE_PAGE
from media_hygiene.services.import_pick_serving import planned_app
from media_hygiene.services.prefixed_page import PrefixedPage
from media_hygiene.services.quarantine_serving import quarantine_page

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.services.fresh_runtime import FreshRuntime


def pages_here(fresh: FreshRuntime, executor: Executor) -> tuple[PrefixedPage, ...]:
    """The quarantine's page and the import's.

    Args:
        fresh: The server's settings, read again when their files change.
        executor: The worker pool.

    Returns:
        The pages.
    """
    return (
        PrefixedPage(
            QUARANTINE_PAGE,
            fresh,
            lambda runtime: QuarantineApp(runtime, quarantine_page(), executor),
        ),
        PrefixedPage(
            IMPORT_PAGE, fresh, lambda runtime: planned_app(runtime, executor)
        ),
    )
