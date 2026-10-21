"""`media-hygiene tags`: the words to find photos by, kept in the cache."""

# pylint: disable=import-outside-toplevel,too-many-locals  # lazy: a command imports
# the code it runs when it runs; those imports count as local variables.

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.cli.options import panel_local_ai
from media_hygiene.i18n import _


def tags_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    path: Annotated[
        list[str] | None,
        typer.Option(
            "--path",
            help=_(
                "Only the photos below this folder (host path, as you mounted it); "
                "repeat it for several. Default: every file of the index."
            ),
            show_default=False,
        ),
    ] = None,
    sample: Annotated[
        int,
        typer.Option(
            "--sample",
            rich_help_panel=panel_local_ai(),
            min=0,
            help=_(
                "Describe this many random photos with the local model, print the "
                "time per photo and the estimate of a full run, and stop."
            ),
            show_default=False,
        ),
    ] = 0,
    no_describe: Annotated[
        bool,
        typer.Option(
            "--no-describe",
            rich_help_panel=panel_local_ai(),
            help=_(
                "Ask the local model nothing new: the words of the folders, names, "
                "dates and places only, and the descriptions already in the cache."
            ),
        ),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            rich_help_panel=panel_local_ai(),
            help=_("Describe the photos without asking, however many."),
        ),
    ] = False,
    meaning: Annotated[
        bool,
        typer.Option(
            "--meaning",
            help=_(
                "Also let a model look at each photo on this computer's processor "
                "(CLIP, once, about 1 minute per 1,000 photos), so that 'search' "
                "finds what a photo shows. Default: [tags] meaning."
            ),
        ),
    ] = False,
) -> None:
    """Tag the photos and videos of the index; never changes a photo.

    Args:
        ctx: Typer context holding the runtime.
        path: `--path`, host folders.
        sample: `--sample N`.
        no_describe: `--no-describe`.
        yes: `--yes`.
        meaning: `--meaning`.
    """
    from media_hygiene.cli.next_steps import carried, suggest
    from media_hygiene.cli.tags_flow import TagRequest, run_tags
    from media_hygiene.paths.mount_kind import MountKind
    from media_hygiene.services.next_command import NextVerb
    from media_hygiene.services.tag_files import require_index
    from media_hygiene.services.writable import ensure_writable

    runtime = runtime_of(ctx)
    output = runtime.output
    with user_errors(output):
        require_index(runtime)
        ensure_writable(runtime, MountKind.CACHE)
        within = tuple(runtime.mapper.to_container(folder) for folder in path or ())
        meaning = meaning or runtime.settings.tags.meaning
        request = TagRequest(within, not no_describe, sample, yes, meaning)
        if not run_tags(runtime, request):
            return
        suggest(
            runtime,
            _(
                "find your photos by these words in your browser; 'inventory' "
                "lists them in its last column."
            ),
            NextVerb(carried(runtime, "search"), port=runtime.settings.review.port),
        )
