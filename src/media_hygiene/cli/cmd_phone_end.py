"""`media-hygiene phone-end`: the last step after `import --phone` (0475, 0477).

Plumbing for `mh` only, hidden from `--help`: run in a terminal after the steps of
`[imports] then`, it offers the new spots' names online (`places` on, its own question),
then says what was done and the slideshow line. With `--copies`, run right after the
audit, before the tags (0480), it only sets aside the new files that are exact copies
(`copies` on, 0478, through `clean`'s journal).
"""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _


# The options are parameters: the documented exception for Typer commands.
def phone_end_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    folder: Annotated[
        str,
        typer.Option(
            "--folder",
            help=_(
                "The folder the phone's files were copied into, as Explorer shows it."
            ),
        ),
    ],
    since: Annotated[
        str | None,
        typer.Option(
            "--since",
            help=_(
                "The period of the import: today, week, month, all or a day; "
                "default: since the last import."
            ),
            show_default=False,
        ),
    ] = None,
    copies: Annotated[
        bool,
        typer.Option(
            "--copies",
            help=_("Only set aside the new files that are exact copies."),
        ),
    ] = False,
) -> None:
    """Name the new places when asked to, then propose the slideshow of the new photos.

    Args:
        ctx: Typer context holding the runtime.
        folder: `--folder`, the host folder of the import.
        since: `--since`, the import's period.
        copies: `--copies`, the copies step alone (0480).
    """
    from media_hygiene.cli.import_places import offer_place_names
    from media_hygiene.config.import_settings import ImportStep
    from media_hygiene.services.import_copies import tell_aside, tell_done
    from media_hygiene.services.import_end import imported, show_title

    runtime = runtime_of(ctx)
    with user_errors(runtime.output):
        files = imported(runtime, folder, since)
        if copies:
            tell_aside(runtime, files)
            return
    if ImportStep.PLACES in runtime.settings.imports.then:
        offer_place_names(runtime, files)
    tell_done(runtime, files)
    title = show_title(runtime, files)
    if not title:
        return
    # The new event only (0480): the folder holds the earlier imports too.
    command = f'mh slideshow --folder "{folder}"' + (
        f" --since {since}" if since else ""
    )
    runtime.output.info(
        _('📺 Your slideshow "{title}" is ready: {command}').format(
            title=title, command=command
        )
    )
