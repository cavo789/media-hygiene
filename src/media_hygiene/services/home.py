"""Serve the home page until Ctrl+C, or until the user chooses a step.

A step chosen is run by `mh` in the terminal (`home_step`, `step_watch`) when `mh` set
`MEDIA_HYGIENE_LAUNCHER_STEPS`, else the page copies the command. It serves `search`
and `browse` too. Photos read-only; its tab closed ends it.
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

from media_hygiene.console.formatting import separators
from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.person.door import with_person
from media_hygiene.review.ending import (
    STOP_PATH,
    STOPPED,
    Ending,
    EndingDoor,
    serve_until_ended,
)
from media_hygiene.review.home_app import AUDIT_PATH, HomeApp
from media_hygiene.review.home_assets import ASSETS_PREFIX
from media_hygiene.review.home_tags_api import RUN_NAMES, TAGS_RUN
from media_hygiene.review.home_texts import home_texts
from media_hygiene.review.lan import lan_access
from media_hygiene.review.lan_app import LAN_PATH, LanApp
from media_hygiene.review.lan_paths import PHONE_PAGES
from media_hygiene.review.lan_phones import phone_book
from media_hygiene.review.lan_problem import with_problem
from media_hygiene.review.local_app import STATE_PATH
from media_hygiene.review.presence import ALIVE_SECONDS, PRESENCE_PATH, Presence
from media_hygiene.review.step_watch import STEP_PATH, keeps_server
from media_hygiene.services.album_pages import album_pages
from media_hygiene.services.home_audit import HomeAudit
from media_hygiene.services.home_lan import say_lan
from media_hygiene.services.home_launch import (
    launcher_relays_fields,
    launcher_relays_steps,
)
from media_hygiene.services.home_pages import HomeServer, home_with_pages
from media_hygiene.services.home_tags import HomeTags
from media_hygiene.services.launcher_host import windows_menu
from media_hygiene.services.reviewing import address_tip, page_url
from media_hygiene.share.album_page import ALBUMS_PAGE

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from media_hygiene.console.page_progress import PageProgress
    from media_hygiene.review.apply_api import ApplyStep
    from media_hygiene.review.ending import Handling
    from media_hygiene.review.home_views import HomeState
    from media_hygiene.services.home_audit import AuditResult
    from media_hygiene.services.home_tags_models import TagsRunner
    from media_hygiene.services.runtime import Runtime

_PACKAGE: Final = "media_hygiene.review"
_TEMPLATE: Final = "home.html.j2"


def home_page(
    *, relays_steps: bool = False, remote: bool = False, runs: frozenset[str] = TAGS_RUN
) -> bytes:
    """Render the home page; its content comes from `GET /api/state`.

    Args:
        relays_steps: The launcher runs a step chosen; else a button copies it.
        remote: Drawn for a phone on the home network (0269): its steps run on the PC.
        runs: The paths of the steps run in the page (`tags`, faces, meaning).

    Returns:
        The page.
    """
    environment = translated_environment(_PACKAGE, escaped=("html", "j2"))
    template = environment.get_template(_TEMPLATE)
    return template.render(
        texts=home_texts(),
        paths={
            "state": STATE_PATH,
            "step": STEP_PATH,
            "audit": AUDIT_PATH,
            **{name: path if path in runs else "" for name, path in RUN_NAMES.items()},
            "alive": PRESENCE_PATH,
            "stop": STOP_PATH,
            "assets": ASSETS_PREFIX,
            "lan": LAN_PATH,
            "albums": ALBUMS_PAGE,
        },
        alive_ms=ALIVE_SECONDS * 1000,
        relays_steps=relays_steps,
        remote=remote,
        phone_pages=PHONE_PAGES if remote else {},
        window=_mh_window(),
        thousands=separators()[0],
    ).encode()


def _mh_window() -> str:
    """Name the window where `mh` runs the step chosen, often behind the browser (0258).

    Returns:
        PowerShell's window from `mh.ps1` (or without `mh`), else the terminal.
    """
    if windows_menu():
        return _("the PowerShell window of mh (in the taskbar)")
    return _("the terminal where mh runs")


@dataclass(frozen=True, slots=True)
class HomeSources:
    """Where the home page's content comes from: the tool folders, and its audit."""

    state: Callable[[], HomeState]
    audit: Callable[[PageProgress], AuditResult]
    apply: Callable[[], ApplyStep | None] | None = None  # browse's *Apply now* (0356)
    runs: Mapping[str, TagsRunner] = field(default_factory=dict)  # by path (0343)


def serve_home(runtime: Runtime, sources: HomeSources, port: int) -> int:
    """Serve the home page until Ctrl+C or a step chosen; its audit stops then.

    Args:
        runtime: Settings, mount points and output.
        sources: Reads the tool folders, and runs the audit, for the page.
        port: The port to listen on, inside the container (0: any free one).

    Returns:
        `STEP_EXIT_BASE + n` for step `n` chosen; 0 on Ctrl+C or the page closed.
    """
    ending = Ending()
    presence = Presence(ending, STOPPED)
    relays = launcher_relays_steps()
    app = HomeApp(
        home_page(relays_steps=relays, runs=frozenset(sources.runs)),
        sources.state,
        runtime.locations.reports_dir,
        ending,
        HomeAudit(sources.audit),
        presence,
        relays_steps=relays,
        relays_fields=relays and launcher_relays_fields(),
        keeps=relays and keeps_server(),
        runs={path: HomeTags(run) for path, run in sources.runs.items()},
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
        if relays:  # `mh` alone: this window runs the steps that ask in it (0284)
            runtime.output.info(
                _(
                    "Keep this window open (minimised is fine): closing it stops "
                    "Media Hygiene."
                )
            )
        address_tip(runtime.output, port)
        say_lan(runtime.output, lan)

    lan = lan_access(port) if port else None  # a phone may open it (0269, 0367)
    code = STOPPED
    try:
        with (
            contextlib.suppress(KeyboardInterrupt),
            runtime.executor_factory() as pool,
            home_with_pages(
                runtime, app, HomeServer(sources.apply, ending, pool)
            ) as both,
        ):
            handler: Handling = album_pages(runtime, both, pool)  # `/albums` (0297)
            if lan is not None:
                handler = LanApp(  # phones paired for good under HTTPS (0431)
                    handler,
                    lan,
                    home_page(remote=True),
                    phones=phone_book(secure=lan.secure),
                    originals=runtime.settings.review.lan_phone_originals,
                )
            handler = with_problem(handler)
            door = with_person(EndingDoor(handler, ending), runtime, pool)
            code = asyncio.run(serve_until_ended(door, port, ready))
    finally:
        app.audit.stop()  # between two files: the index keeps what it committed
        for run in app.runs.values():
            run.stop()  # after the photo in flight: the cache keeps each answer
    if presence.closed:
        runtime.output.info(_("The home page's tab was closed: the home page stopped."))
    return code
