"""`media-hygiene share`: an album made ready to send, a folder and a zip (0296)."""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Final

import typer

from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.share_album import Prepared

# An attachment limit of several webmails, to check against the user's own (0296).
MAIL_LIMIT_BYTES: Final = 25 * 1000 * 1000


def share_command(
    ctx: typer.Context,
    *,
    album: Annotated[
        str,
        typer.Option(
            "--album",
            help=_(
                'The album to send, made in search, browse or the burst review: "Crete '
                '2023".'
            ),
            show_default=False,
        ),
    ],
    keep_gps: Annotated[
        bool,
        typer.Option(
            "--keep-gps",
            help=_(
                "Keep the GPS position in the copies; removed by default, a photo "
                "sent must not say where the house is."
            ),
        ),
    ] = False,
) -> None:
    """Prepare an album for sending: resized copies without GPS, a folder and a zip.

    Args:
        ctx: Typer context holding the runtime.
        album: `--album`, the album's name.
        keep_gps: `--keep-gps`, the position kept in the copies.
    """
    from media_hygiene.services.share_album import SendRequest, prepare_album

    runtime = runtime_of(ctx)
    runtime.output.info(
        _("Preparing the photos of the album {name}…").format(name=album)
    )
    with user_errors(runtime.output):
        prepared = prepare_album(runtime, SendRequest(album, keep_gps=keep_gps))
    _say(runtime, prepared)


def _say(runtime: Runtime, prepared: Prepared) -> None:
    """Say what was written, read back from the disk, and what was left out.

    Args:
        runtime: Settings, mount points and output.
        prepared: The album ready to send.
    """
    from media_hygiene.console.formatting import human_size

    output = runtime.output
    sent = prepared.sent
    folder = runtime.mapper.to_host(sent.folder)
    archive = runtime.mapper.to_host(sent.archive)
    if sent.replaced:
        output.info(_("The earlier copies of this album were replaced."))
    output.success(
        ngettext(
            "{n} photo ready to send ({size}), read back from {folder}.",
            "{n} photos ready to send ({size}), read back from {folder}.",
            sent.photos,
        ).format(n=sent.photos, size=human_size(sent.size), folder=folder)
    )
    output.success(
        _("The zip, read back: {zip} ({size}, {n} files).").format(
            zip=archive, size=human_size(sent.zip_size), n=sent.zipped
        )
    )
    if prepared.keep_gps:
        output.info(_("📍 The GPS positions were kept, as asked."))
    else:
        output.info(_("📍 The GPS positions were removed: --keep-gps keeps them."))
    _left_out(output, prepared)
    if sent.zip_size > MAIL_LIMIT_BYTES:
        output.warning(
            _(
                "The zip is larger than 25 MB: some webmails refuse an attachment "
                "that large (check your mail's own limit). Send the folder another "
                "way (a USB stick, a shared drive), or an album of fewer photos."
            )
        )
    output.next_step(
        _(
            "attach {zip} to a mail, or add the photos of {folder} to an album on "
            "your social network."
        ).format(zip=archive, folder=folder)
    )


def _left_out(output: Output, prepared: Prepared) -> None:
    """Count what the album holds but the folder does not.

    Args:
        output: Where to say it.
        prepared: The album ready to send.
    """
    if prepared.videos:
        output.info(
            ngettext(
                "{n} video not included: only the photos are copied (a video alone "
                "may pass a mail's limit).",
                "{n} videos not included: only the photos are copied (a video alone "
                "may pass a mail's limit).",
                prepared.videos,
            ).format(n=prepared.videos)
        )
    if prepared.missing:
        output.warning(
            ngettext(
                "{n} file of the album is missing (moved out of the folders "
                "analysed, or deleted): not included.",
                "{n} files of the album are missing (moved out of the folders "
                "analysed, or deleted): not included.",
                prepared.missing,
            ).format(n=prepared.missing)
        )
    if prepared.unreadable:
        output.warning(
            ngettext(
                "{n} photo could not be read: not included.",
                "{n} photos could not be read: not included.",
                prepared.unreadable,
            ).format(n=prepared.unreadable)
        )
