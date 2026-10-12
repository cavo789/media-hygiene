"""`media-hygiene tags`: the words to find photos by, kept in the cache."""

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.cli.next_steps import carried, suggest
from media_hygiene.cli.review_options import PAGE_PORT
from media_hygiene.cli.tags_flow import TagRequest, run_tags
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.next_command import NextVerb
from media_hygiene.services.tag_files import require_index
from media_hygiene.services.writable import ensure_writable


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
            help=_("Describe the photos without asking, however many."),
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
    """
    runtime = runtime_of(ctx)
    output = runtime.output
    with user_errors(output):
        require_index(runtime)
        ensure_writable(runtime, MountKind.CACHE)
        within = tuple(runtime.mapper.to_container(folder) for folder in path or ())
        request = TagRequest(within, not no_describe, sample, yes)
        if not run_tags(runtime, request):
            return
        suggest(
            runtime,
            _(
                "find your photos by these words in your browser; 'inventory' "
                "lists them in its last column."
            ),
            NextVerb(carried(runtime, "search"), port=PAGE_PORT),
        )
