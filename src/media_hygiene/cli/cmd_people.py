"""`media-hygiene people`: find the faces of the photos, group them, show the groups."""

# pylint: disable=import-outside-toplevel,too-many-locals  # lazy: a command imports
# the code it runs when it runs; those imports count as local variables.

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli import review_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _


# The options are parameters: the documented exception for Typer commands.
def people_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    path: Annotated[
        list[str] | None,
        typer.Option(
            "--path",
            help=_(
                "Only the photos below this folder (host path, as you mounted it); "
                "repeat it for several. Default: every photo of the index."
            ),
            show_default=False,
        ),
    ] = None,
    sample: Annotated[
        int,
        typer.Option(
            "--sample",
            min=0,
            help=_(
                "Analyse this many random photos, print the time per photo and the "
                "estimate of a full run, and stop."
            ),
            show_default=False,
        ),
    ] = 0,
    forget: Annotated[
        bool,
        typer.Option(
            "--forget",
            help=_(
                "Delete every face from the cache, then show that none is left; "
                "asks before deleting the names of config.toml too."
            ),
        ),
    ] = False,
    port: Annotated[int | None, review_options.port()] = None,
) -> None:
    """Find the faces the cache lacks, group them, show and name them until Ctrl+C.

    Args:
        ctx: Typer context holding the runtime.
        path: `--path`, host folders.
        sample: `--sample N`.
        forget: `--forget`.
        port: `--port`, inside the container.

    Raises:
        Exit: With `STEP_EXIT_BASE + n` when *Apply now* chose step `n` (opened
            from the home page): `mh` runs it, then opens the home page again.
    """
    from media_hygiene.cli.apply_step import end_on_applied, page_apply
    from media_hygiene.cli.cmd_search import suggest_clean
    from media_hygiene.cli.next_steps import carried, suggest
    from media_hygiene.cli.people_flow import PeopleRequest, run_people
    from media_hygiene.paths.mount_kind import MountKind
    from media_hygiene.services.next_command import NextVerb
    from media_hygiene.services.people_files import require_people_index
    from media_hygiene.services.people_page import PeopleStart, serve_people
    from media_hygiene.services.writable import ensure_writable

    runtime = runtime_of(ctx)
    port = review_options.page_port(runtime, port)
    output = runtime.output
    with user_errors(output):
        require_people_index(runtime)
        ensure_writable(runtime, MountKind.CACHE)
        within = tuple(runtime.mapper.to_container(folder) for folder in path or ())
        result = run_people(runtime, PeopleRequest(within, sample, forget))
        if sample:
            suggest(
                runtime,
                _("analyse every photo, then see the faces alike in your browser."),
                NextVerb(carried(runtime, "people"), port=port),
            )
        if result is None or not result.groups.people:
            return
        # Opened from the home page: `mh` runs the step *Apply now* ends on (0243).
        served = serve_people(runtime, result, PeopleStart(port, page_apply(runtime)))
        output.blank()
        output.success(_("Page stopped; nothing was changed."))
        end_on_applied(runtime, served.code)
        if served.chosen:
            suggest_clean(runtime, served.chosen)
