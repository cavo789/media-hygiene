"""`media-hygiene phone-end`: the last step after `import --phone` (0475, 0477).

Plumbing for `mh` only, hidden from `--help`: run in a terminal after the steps of
`[imports] then`, it offers the new spots' names online (`places` on, its own question),
sets aside the new files that are exact copies (`copies` on, 0478, through `clean`'s
journal), then says what was done and the slideshow line.
"""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _


def phone_end_command(
    ctx: typer.Context,
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
) -> None:
    """Name the new places when asked to, then propose the slideshow of the new photos.

    Args:
        ctx: Typer context holding the runtime.
        folder: `--folder`, the host folder of the import.
        since: `--since`, the import's period.
    """
    from media_hygiene.cli.import_places import offer_place_names
    from media_hygiene.config.import_settings import ImportStep
    from media_hygiene.services.import_copies import tell_done
    from media_hygiene.services.import_end import new_files, show_title
    from media_hygiene.services.import_since import first_day, last_import, today_local

    runtime = runtime_of(ctx)
    with user_errors(runtime.output):
        first = first_day(
            since, today_local(), last_import(runtime.locations.journal_dir)
        )
    files = new_files(runtime.mapper.to_container(folder), first)
    if ImportStep.PLACES in runtime.settings.imports.then:
        offer_place_names(runtime, files)
    with user_errors(runtime.output):
        tell_done(runtime, files)
    title = show_title(runtime, files)
    if not title:
        return
    runtime.output.info(
        _(
            '📺 Your slideshow "{title}" is ready: mh slideshow --folder "{folder}"'
        ).format(title=title, folder=folder)
    )
