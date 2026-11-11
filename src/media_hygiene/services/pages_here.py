"""The pages the home server serves under their prefix (0591, 0590, 0594, 0600)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.review.quarantine_app import QuarantineApp
from media_hygiene.review.served_more import IMPORT_PAGE, QUARANTINE_PAGE
from media_hygiene.services.import_pick_serving import planned_app
from media_hygiene.services.people_here import people_here
from media_hygiene.services.prefixed_page import PrefixedPage
from media_hygiene.services.quarantine_serving import quarantine_page
from media_hygiene.services.settings_here import SettingsHere

if TYPE_CHECKING:
    from media_hygiene.services.fresh_runtime import FreshRuntime
    from media_hygiene.services.home_pages import HomeServer
    from media_hygiene.services.prefixed_page import ServedPage


def pages_here(fresh: FreshRuntime, server: HomeServer) -> tuple[ServedPage, ...]:
    """The quarantine's page, the import's, the people's, the settings' (0670).

    Args:
        fresh: The server's settings, read again when their files change.
        server: The home server's *Apply now*, end and pool.

    Returns:
        The pages.
    """
    executor = server.executor
    return (
        PrefixedPage(
            QUARANTINE_PAGE,
            fresh,
            lambda runtime: QuarantineApp(runtime, quarantine_page(), executor),
        ),
        PrefixedPage(
            IMPORT_PAGE, fresh, lambda runtime: planned_app(runtime, executor)
        ),
        people_here(fresh, server),
        SettingsHere(fresh),
    )
