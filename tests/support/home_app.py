"""The home page's app as the tests build it: the state of a runtime, an audit, tags."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.cli.home_state import home_state
from media_hygiene.review.ending import STOPPED
from media_hygiene.review.home_app import HomeApp
from media_hygiene.review.presence import Presence
from media_hygiene.services.home import home_page

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.ending import Ending
    from media_hygiene.services.home_audit import HomeAudit
    from media_hygiene.services.home_tags import HomeTags
    from media_hygiene.services.runtime import Runtime


def home_app_of(
    runtime: Runtime, audit: HomeAudit, tags: HomeTags | None = None
) -> Callable[[Ending], HomeApp]:
    """The app `serve` builds once the ending exists.

    Args:
        runtime: Its state and reports folder.
        audit: The page's audit.
        tags: The page's tags, if any.

    Returns:
        Builds the app.
    """
    return lambda ending: HomeApp(
        home_page(),
        partial(home_state, runtime),
        runtime.locations.reports_dir,
        ending,
        audit,
        Presence(ending, STOPPED),
        tags=tags,
    )
