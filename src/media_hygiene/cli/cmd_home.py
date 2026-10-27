"""`media-hygiene home`: the home page in the browser, where every step starts.

The page shows what `status` says, the next step as a big button, every step of the
guides as `mh menu` numbers them, the reports and a few previews. When `mh` set
`MEDIA_HYGIENE_LAUNCHER_STEPS`, a step's button ends the command with the code
`STEP_EXIT_BASE + n`: `mh` runs step `n` in the terminal, mounted as it needs, then
opens the home page again.
Without it, the button copies the command and the page keeps running.
"""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Annotated

import typer

from media_hygiene.cli import review_options
from media_hygiene.cli.context import runtime_of
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.home_views import HomeState
    from media_hygiene.services.fresh_runtime import FreshRuntime
    from media_hygiene.services.home_tags_models import TagsRunner
    from media_hygiene.services.runtime import Runtime


def home_command(
    ctx: typer.Context,
    *,
    port: Annotated[int | None, review_options.port()] = None,
) -> None:
    """Serve the home page until Ctrl+C or a step chosen.

    Args:
        ctx: Typer context holding the runtime.
        port: `--port`, inside the container.

    Raises:
        Exit: With `STEP_EXIT_BASE + n` when step `n` was chosen on the page.
    """
    from media_hygiene.cli.apply_step import page_apply
    from media_hygiene.cli.home_audit import page_audit
    from media_hygiene.cli.home_state import home_state
    from media_hygiene.review.home_views import STEP_EXIT_BASE
    from media_hygiene.services.fresh_runtime import FreshRuntime
    from media_hygiene.services.home import HomeSources, serve_home

    runtime = runtime_of(ctx)
    port = review_options.page_port(runtime, port)
    # The session long: the settings read again as their files change (0358).
    fresh = FreshRuntime(runtime)
    state = partial(_state_now, home_state, fresh)
    runs = _page_runs(runtime, fresh)
    code = serve_home(
        runtime,
        HomeSources(state, page_audit(fresh), page_apply(runtime), runs),
        port,
    )
    runtime.output.blank()
    if code < STEP_EXIT_BASE:
        runtime.output.success(_("Home page closed; your photos were not changed."))
        return
    command = state().command_of(code - STEP_EXIT_BASE)
    runtime.output.info(
        _("Step {number} chosen on the home page: {command}").format(
            number=code - STEP_EXIT_BASE, command=command
        )
    )
    raise typer.Exit(code)


def _page_runs(runtime: Runtime, fresh: FreshRuntime) -> dict[str, TagsRunner]:
    """The read-only steps the page runs: tags, faces, and meaning when it is on.

    Args:
        runtime: The settings at start (`[tags] meaning`, 0425).
        fresh: The runtime, its settings read again when changed.

    Returns:
        The runners, by path.
    """
    from media_hygiene.cli.home_meaning import page_meaning
    from media_hygiene.cli.home_people import page_people
    from media_hygiene.cli.home_tags import page_tags
    from media_hygiene.review.home_tags_api import MEANING_PATH, PEOPLE_PATH, TAGS_PATH

    runs = {TAGS_PATH: page_tags(fresh), PEOPLE_PATH: page_people(fresh)}
    if runtime.settings.tags.meaning:
        runs[MEANING_PATH] = page_meaning(fresh)
    return runs


def _state_now(read: Callable[[Runtime], HomeState], fresh: FreshRuntime) -> HomeState:
    """The home page's state, with the settings the files hold now.

    Args:
        read: Reads the state (`home_state`).
        fresh: The runtime, its settings read again when changed.

    Returns:
        The state, with the line of a settings file that does not load (0364).
    """
    state = read(fresh.runtime())
    if not fresh.error:
        return state
    return state.model_copy(update={"settings_error": fresh.error})
