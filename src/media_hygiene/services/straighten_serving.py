"""The *Photos to straighten* page (0810), served by the home server.

It lives under `/straighten/`.

Opened from the home page, its *Apply now* ends on the menu's step `straighten`
(`people --straighten`): `mh` turns, in its window and after its question, every photo
the page shows; nothing pending (every turn refused or written), no button.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.apply_step import named_step
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.apply_api import ApplyDesk, ApplyingApp, ApplyOffer
from media_hygiene.review.apply_relay import home_relay
from media_hygiene.review.files import FILE_PATH
from media_hygiene.review.home_views import APPLY_PATH
from media_hygiene.review.local_app import STATE_PATH
from media_hygiene.review.page_header import headed_page
from media_hygiene.review.straighten_app import REFUSE_PATH, TURN_PATH, StraightenApp
from media_hygiene.search.undo_api import UNDO_PATH
from media_hygiene.services.page_undo import PageUndo
from media_hygiene.services.turn_pick import turn_jobs_now

if TYPE_CHECKING:
    from media_hygiene.services.home_pages import HomeServer
    from media_hygiene.services.runtime import Runtime

PAGE_TEMPLATE: Final = "straighten.html.j2"
STEP_NAME: Final = "straighten"  # the catalog's step *Apply now* ends on


def straighten_page(offered: bool) -> bytes:  # noqa: FBT001 - one fact
    """Render the page; its paths relative to it.

    Args:
        offered: Opened from the home page: *Apply now* in the bar.

    Returns:
        The page, in the language in use.
    """
    environment = translated_environment("media_hygiene.review", escaped=("html", "j2"))
    paths = {
        "state_path": STATE_PATH,
        "file_path": FILE_PATH,
        "turn_path": TURN_PATH,
        "refuse_path": REFUSE_PATH,
        "undo_path": UNDO_PATH,
        "apply_path": APPLY_PATH,
    }
    values: dict[str, object] = {
        name: path.removeprefix("/") for name, path in paths.items()
    }
    values["apply_offered"] = offered
    return headed_page(environment, PAGE_TEMPLATE, values)


def straighten_app(runtime: Runtime, server: HomeServer) -> ApplyingApp:
    """The page's app, with *Apply now* when the home page opened it.

    Args:
        runtime: The server's settings now.
        server: The home server's *Apply now*, end and pool.

    Returns:
        The app.
    """
    offered = server.apply is not None
    step = partial(named_step, runtime, STEP_NAME) if offered else None
    app = StraightenApp(runtime, straighten_page(offered), server.executor)
    offer = ApplyOffer(step, lambda: bool(turn_jobs_now(runtime)), PageUndo(runtime))
    relay = home_relay(runtime.locations.reports_dir)
    return ApplyingApp(app, ApplyDesk(offer, server.ending, relay))
