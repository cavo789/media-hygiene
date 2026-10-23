"""`media-hygiene shrink`: lighten heavy videos, originals in the quarantine (0303)."""

# pylint: disable=import-outside-toplevel,too-many-locals  # lazy: a command imports
# the code it runs when it runs; those imports count as local variables.

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _


def shrink_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    folder: Annotated[
        list[str] | None,
        typer.Option(
            "--folder",
            help=_(
                "Only the videos below this folder (host path, as you mounted it); "
                "repeat it for several. Default: every mounted folder."
            ),
            show_default=False,
        ),
    ] = None,
    lighter: Annotated[
        bool,
        typer.Option(
            "--lighter",
            help=_(
                "Lighter still for a large picture: at most 720 lines (lighter_lines "
                "in config.toml). For clips whose quality matters less."
            ),
        ),
    ] = False,
    apply: Annotated[
        bool,
        typer.Option(
            "--apply",
            help=_("Lighten them; without it, only list them with the gain expected."),
        ),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help=_("Lighten without asking first.")),
    ] = False,
) -> None:
    """List the heavy videos worth lightening; with --apply, lighten them.

    Args:
        ctx: Typer context holding the runtime.
        folder: `--folder`, host folders.
        lighter: `--lighter`, a smaller picture and a stronger compression.
        apply: `--apply`, re-encode them.
        yes: `--yes`, no question.

    Raises:
        typer.Exit: The user declined.
    """
    from media_hygiene.cli.next_steps import carried, safety, suggest
    from media_hygiene.console.progress import RichProgress
    from media_hygiene.console.shrink_view import show_candidates, show_result
    from media_hygiene.scan.progress import NullProgress
    from media_hygiene.services.interrupt import StopRequest
    from media_hygiene.services.next_command import CHANGING, NextVerb
    from media_hygiene.services.shrink import ShrinkAsk, ShrinkJobs, ShrinkService

    runtime = runtime_of(ctx)
    output = runtime.output
    within = tuple(runtime.mapper.to_container(path) for path in folder or ())
    asked = "".join(f' --folder "{path}"' for path in folder or ())
    level = f"{' --lighter' if lighter else ''}{asked}"
    with user_errors(output):
        service = ShrinkService(runtime, NullProgress())
        videos = service.candidates(ShrinkAsk(within, lighter=lighter))
        if not videos:
            output.success(_("No video worth lightening."))
            return
        show_candidates(runtime, videos)
        if not apply:
            output.info(_("🔒 Nothing was changed: this is only the list."))
            suggest(
                runtime,
                _(
                    "the same command with --apply re-encodes them, each original "
                    "in the quarantine ('undo' brings it back)."
                ),
                NextVerb(carried(runtime, f"shrink{level} --apply"), CHANGING),
            )
            return
        tools = service.ensure_ready()
    if not yes and not typer.confirm(_("Lighten them?"), default=True):
        raise typer.Exit
    output.info(
        _(
            "🛟 Each video is re-encoded beside itself and checked (length, sound, "
            "date, place) before it replaces the original, which goes to the "
            "quarantine. Ctrl+C stops after the video being encoded."
        )
    )
    with RichProgress(output.console) as progress, StopRequest() as stop:
        jobs = ShrinkJobs(videos, tools, lighter=lighter)
        result = ShrinkService(runtime, progress).execute(jobs, stop.requested)
    show_result(runtime, result)
    safety(
        runtime,
        _(
            "Changed your mind? 'media-hygiene undo {run_id}' removes the lighter "
            "videos and brings the originals back:"
        ).format(run_id=result.run_id),
        NextVerb(carried(runtime, f"undo {result.run_id}"), CHANGING),
    )
    if result.outcome.quarantined:  # an original aside, even one not replaced
        suggest(
            runtime,
            _(
                "once you have watched a few, 'purge' frees the space: the "
                "originals are still in the quarantine until then."
            ),
            NextVerb(carried(runtime, f"purge {result.run_id}"), CHANGING),
        )
