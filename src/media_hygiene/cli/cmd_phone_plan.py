r"""`media-hygiene phone-plan`: which files of a phone `import --phone` copies (0219).

Plumbing for `mh` only, hidden from `--help`: `mh.ps1` lists the phone's `DCIM` and
pipes one `path<TAB>size<TAB>date` line per file; the plan comes back on stdout, one
line per file, its case first (`new`, `library`, `set-aside`, `destination`) and its
reason after. Every message goes to stderr. Nothing is written but the index's
memory of the journals.
"""

# pylint: disable=import-outside-toplevel,too-many-locals  # lazy: a command loads its
# code when it runs; those imports count as local variables.

from __future__ import annotations

import sys
from typing import Annotated, Final

import typer

from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _, ngettext

_ENCODING: Final = "utf-8"


def phone_plan_command(
    ctx: typer.Context,
    *,
    destination: Annotated[
        str | None,
        typer.Option(
            "--destination",
            help=_(
                "The folder the phone's files are copied into, as Explorer shows "
                "it (mounted read-only): a file it holds is not copied again."
            ),
            show_default=False,
        ),
    ] = None,
    since: Annotated[
        str | None,
        typer.Option(
            "--since",
            help=_(
                "Only the files of a period: today, week, month, all or a day "
                "(2026-10-29); default: since the last import."
            ),
            show_default=False,
        ),
    ] = None,
) -> None:
    """Read the phone's listing on stdin, print the case of each file on stdout.

    Args:
        ctx: Typer context holding the runtime.
        destination: `--destination`, the host folder of the import.
        since: `--since`, the period (0476); None: since the last import.
    """
    from media_hygiene.services.launcher_phone_then import THEN
    from media_hygiene.services.phone_known import (
        PhoneQuery,
        known_of,
        without_hidden,
    )
    from media_hygiene.services.phone_period import held_back
    from media_hygiene.services.phone_plan import SEPARATOR, decide, read_listing

    runtime = runtime_of(ctx)
    text = sys.stdin.buffer.read().decode(_ENCODING, errors="replace")
    files, skipped = read_listing(text.splitlines())
    if skipped:
        runtime.output.warning(
            ngettext(
                "{count} line of the phone's listing could not be read: skipped.",
                "{count} lines of the phone's listing could not be read: skipped.",
                skipped,
            ).format(count=skipped)
        )
    files, hidden = without_hidden(files)
    if hidden:
        runtime.output.info(
            ngettext(
                "{count} hidden file of the phone left out (its name starts "
                "with a dot).",
                "{count} hidden files of the phone left out (their names start "
                "with a dot).",
                hidden,
            ).format(count=hidden)
        )
    folder = runtime.mapper.to_container(destination) if destination else None
    known = known_of(runtime, PhoneQuery(files, folder))
    with user_errors(runtime.output):
        verdicts = held_back(runtime, decide(files, known), since)
    lines = "".join(f"{verdict.line()}\n" for verdict in verdicts)
    # The steps after the copies (0475): `mh` runs them in this order.
    lines += "".join(
        f"{THEN}{SEPARATOR}{step.value}\n" for step in runtime.settings.imports.then
    )
    sys.stdout.buffer.write(lines.encode(_ENCODING))
    sys.stdout.flush()
