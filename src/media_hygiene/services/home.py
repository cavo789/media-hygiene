"""Serve the home page until Ctrl+C or a step chosen (`home_step`, `step_watch`)."""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, Final

from media_hygiene.console.formatting import separators
from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.person.door import with_person
from media_hygiene.review.ai_state_api import AI_STATE_PATH
from media_hygiene.review.album_show import TV_CHOICES, TV_CHOOSE
from media_hygiene.review.ending import (
    STOP_PATH,
    STOPPED,
    Ending,
    EndingDoor,
    serve_until_ended,
)
from media_hygiene.review.home_app import AUDIT_PATH, FAVOURITES_PATH, HomeApp
from media_hygiene.review.home_assets import ASSETS_PREFIX
from media_hygiene.review.home_more_api import MORE_PATHS
from media_hygiene.review.home_tags_api import INLINE_PATH, RUN_NAMES, TAGS_RUN
from media_hygiene.review.home_texts import home_texts
from media_hygiene.review.import_chain_api import IMPORT_CHAIN_PATH, ChainDoor
from media_hygiene.review.import_steps_api import IMPORT_STEPS_PATH
from media_hygiene.review.lan import lan_access
from media_hygiene.review.lan_paths import LAN_PATH, PHONE_PAGES
from media_hygiene.review.lan_problem import with_problem
from media_hygiene.review.lan_switch_api import LAN_SWITCH_PATH
from media_hygiene.review.local_app import STATE_PATH
from media_hygiene.review.presence import ALIVE_SECONDS, PRESENCE_PATH, Presence
from media_hygiene.review.scan_scope_api import SCOPE_PATH
from media_hygiene.review.step_watch import STEP_PATH, keeps_server
from media_hygiene.search.late_desk import LATE_PATH
from media_hygiene.services.album_pages import album_pages
from media_hygiene.services.home_audit import HomeAudit
from media_hygiene.services.home_lan import lan_door, say_lan
from media_hygiene.services.home_launch import (
    launcher_relays_fields,
    launcher_relays_steps,
    mh_window,
)
from media_hygiene.services.home_pages import HomeServer, home_with_pages
from media_hygiene.services.home_tags import HomeTags
from media_hygiene.services.import_chain import chain_file
from media_hygiene.services.reviewing import address_tip, page_url
from media_hygiene.share.album_page import ALBUM_LIST_PATH, ALBUMS_PAGE
from media_hygiene.slideshow.routes import SLIDES_PATH

if TYPE_CHECKING:
    from media_hygiene.services.home_sources import HomeSources
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
            "inline": INLINE_PATH,  # a short step run here (0505)
            "audit": AUDIT_PATH,
            "favourites": FAVOURITES_PATH,
            **MORE_PATHS,
            "scope": SCOPE_PATH,
            "aiState": AI_STATE_PATH,  # [classify.ai] model on the tags dialog (0608)
            "lanSwitch": LAN_SWITCH_PATH,  # [review] lan on the page (0605)
            "importSteps": IMPORT_STEPS_PATH,  # [imports] then (0481)
            "importChain": IMPORT_CHAIN_PATH,  # where it is (0604)
            **{name: path if path in runs else "" for name, path in RUN_NAMES.items()},
            "alive": PRESENCE_PATH,
            "stop": STOP_PATH,
            "assets": ASSETS_PREFIX,
            "lan": LAN_PATH,
            "albums": ALBUMS_PAGE,
            "albumList": ALBUM_LIST_PATH,  # a phone starts an album on the TV (0444)
            "tvChoices": TV_CHOICES,
            "tvChoose": TV_CHOOSE,
            "slides": SLIDES_PATH,  # the slideshow answering: the phone follows
            "late": LATE_PATH,  # new photos during an event (0558), the search app's
        },
        alive_ms=ALIVE_SECONDS * 1000,
        relays_steps=relays_steps,
        remote=remote,
        phone_pages=PHONE_PAGES if remote else {},
        window=mh_window(),
        thousands=separators()[0],
    ).encode()


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
        config_file=runtime.locations.config_file,
        samples=sources.samples,
        chain=ChainDoor(
            chain_file(runtime),
            runtime.locations.reports_dir,
            relays and keeps_server(),
        ),
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
                runtime, app, server := HomeServer(sources.apply, ending, pool, lan)
            ) as both,
        ):
            door = with_person(  # the TV on the plain door (0417)
                EndingDoor(
                    with_problem(
                        lan_door(  # `/albums` (0297), a phone's door (0431, 0462)
                            runtime,
                            album_pages(runtime, both, server),
                            None if lan is None else (lan, home_page(remote=True)),
                        )
                    ),
                    ending,
                    plain=both.slideshow.tv,
                ),
                runtime,
                pool,
            )
            code = asyncio.run(serve_until_ended(door, port, ready))
    finally:
        app.audit.stop()  # between two files: the index keeps what it committed
        for run in app.runs.values():
            run.stop()  # after the photo in flight: the cache keeps each answer
    if presence.closed:
        runtime.output.info(_("The home page's tab was closed: the home page stopped."))
    return code
