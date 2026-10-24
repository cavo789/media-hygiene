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
    trial: Annotated[
        bool,
        typer.Option(
            "--try",
            help=_(
                "Encode the first ones (try_count in config.toml) as drafts, in "
                "/cache only, and compare before and after in the browser; lighten "
                "from the page. The drafts are removed when the page closes."
            ),
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
        trial: `--try`, drafts compared in the browser first.
        yes: `--yes`, no question.
    """
    from media_hygiene.cli.next_steps import carried, suggest
    from media_hygiene.cli.shrink_flow import Asked, lighten, try_then_lighten
    from media_hygiene.console.shrink_view import show_candidates
    from media_hygiene.scan.progress import NullProgress
    from media_hygiene.services.next_command import CHANGING, NextVerb
    from media_hygiene.services.shrink import ShrinkAsk, ShrinkJobs, ShrinkService
    from media_hygiene.services.shrink_try import ensure_cache, sweep_drafts

    runtime = runtime_of(ctx)
    output = runtime.output
    within = tuple(runtime.mapper.to_container(path) for path in folder or ())
    asked = "".join(f' --folder "{path}"' for path in folder or ())
    level = f"{' --lighter' if lighter else ''}{asked}"
    with user_errors(output):
        if trial:
            ensure_cache(runtime)  # before the index: the drafts' line, not "audit"
        sweep_drafts(runtime)
        service = ShrinkService(runtime, NullProgress())
        videos = service.candidates(ShrinkAsk(within, lighter=lighter))
        if not videos:
            output.success(_("No video worth lightening."))
            return
        show_candidates(runtime, videos)
        if trial:
            try_then_lighten(runtime, Asked(videos, lighter=lighter, yes=yes))
            return
        if not apply:
            output.info(_("🔒 Nothing was changed: this is only the list."))
            suggest(
                runtime,
                _(
                    "the same command with --try compares a few before and after in "
                    "the browser; with --apply, it re-encodes them, each original "
                    "in the quarantine ('undo' brings it back)."
                ),
                NextVerb(carried(runtime, f"shrink{level} --try"), CHANGING),
            )
            return
        tools = service.ensure_ready()
    lighten(runtime, ShrinkJobs(videos, tools, lighter=lighter), yes=yes)
