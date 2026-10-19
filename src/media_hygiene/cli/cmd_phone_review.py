r"""`phone-review`: the page where the user ticks what leaves the phone (0248).

Plumbing for `mh` only, hidden from `--help`: `mh` pipes the plan's lines on stdin
(UTF-8) and publishes the port; the page saves `phone-decisions.json` in `/reports`.
On "Delete from the phone", the files ticked, read back from the disk, are printed on
stdout as the plan named them; nothing else is. Every message goes to stderr.
"""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

import sys
from typing import Annotated, Final

import typer

from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.cli.review_options import PAGE_PORT, port
from media_hygiene.i18n import _

_ENCODING: Final = "utf-8"


def phone_review_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    phone: Annotated[
        str,
        typer.Option("--phone", help=_("The phone's name, as Windows shows it.")),
    ],
    destination: Annotated[
        str | None,
        typer.Option(
            "--destination",
            help=_(
                "The folder of the import, as Explorer shows it (mounted "
                "read-only): its copies are shown on the page."
            ),
            show_default=False,
        ),
    ] = None,
    page_port: Annotated[int, port()] = PAGE_PORT,
) -> None:
    """Serve the page of the files the PC may hold; print those ticked to delete.

    Args:
        ctx: Typer context holding the runtime.
        phone: `--phone`, the phone's name.
        destination: `--destination`, the host folder of the import.
        page_port: `--port`, the port of the page.
    """
    from media_hygiene.services.phone_free import read_ticked
    from media_hygiene.services.phone_review import PhoneReview, serve_phone_review

    runtime = runtime_of(ctx)
    text = sys.stdin.buffer.read().decode(_ENCODING, errors="replace")
    files, _skipped = read_ticked(text.splitlines())  # a new file never leaves
    if not files:
        runtime.output.info(
            _("Nothing on the phone that the PC holds: nothing to free.")
        )
        return
    folder = runtime.mapper.to_container(destination) if destination else None
    with user_errors(runtime.output):
        lines = serve_phone_review(
            runtime, PhoneReview(phone, files, folder, page_port)
        )
    if not lines:
        runtime.output.info(_("Nothing was deleted from the phone."))
    sys.stdout.buffer.write("".join(f"{line}\n" for line in lines).encode(_ENCODING))
    sys.stdout.flush()
