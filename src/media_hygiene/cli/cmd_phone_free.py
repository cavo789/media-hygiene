r"""`phone-prove` and `phone-done`: freeing a phone, proven then journaled (0248).

Plumbing for `mh` only, hidden from `--help`, like `phone-plan`. `phone-prove` reads
the plan's lines of the files ticked (stdin, UTF-8), proves each staged copy, writes
the proven ones `pending` in a journal run of kind `phone`, and prints the run, then
one line per file (`proven…` or `kept…`). `phone-done --run <run>` reads the paths
gone from the phone and writes them `done`, one line each on stdout. Every message
goes to stderr. Nothing on the PC is changed but the journal.
"""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

import sys
from typing import Annotated, Final

import typer

from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _, ngettext

_ENCODING: Final = "utf-8"
RUN_LINE: Final = "run"
DONE_LINE: Final = "done"


def _stdin() -> list[str]:
    """Read the lines `mh` piped in, in UTF-8.

    Returns:
        Them.
    """
    return sys.stdin.buffer.read().decode(_ENCODING, errors="replace").splitlines()


def _print(lines: list[str]) -> None:
    """Write lines on stdout, in UTF-8, for `mh` to read.

    Args:
        lines: The lines, without their ends.
    """
    sys.stdout.buffer.write("".join(f"{line}\n" for line in lines).encode(_ENCODING))
    sys.stdout.flush()


def phone_prove_command(  # pylint: disable=too-many-arguments,too-many-locals
    ctx: typer.Context,
    *,
    phone: Annotated[
        str,
        typer.Option("--phone", help=_("The phone's name, as Windows shows it.")),
    ],
    staging: Annotated[
        str,
        typer.Option(
            "--staging",
            help=_(
                "The folder the files ticked were just copied into from the phone, "
                "as Explorer shows it (mounted read-only)."
            ),
        ),
    ],
    destination: Annotated[
        str | None,
        typer.Option(
            "--destination",
            help=_(
                "The folder of the import, as Explorer shows it (mounted "
                "read-only): its copies prove the files it imported."
            ),
            show_default=False,
        ),
    ] = None,
    run: Annotated[
        str | None,
        typer.Option(
            "--run",
            help=_("The run to go on with, for the next files; none: a new run."),
            show_default=False,
        ),
    ] = None,
) -> None:
    """Prove each file ticked by its content; journal the proven ones `pending`.

    Args:
        ctx: Typer context holding the runtime.
        phone: `--phone`, the phone's name.
        staging: `--staging`, the host folder of the staged copies.
        destination: `--destination`, the host folder of the import.
        run: `--run`, the phone run to go on with.

    Raises:
        MountError: The journal is not mounted.
    """
    from media_hygiene.errors import MountError
    from media_hygiene.paths.mount_kind import MountKind
    from media_hygiene.services.phone_free import (
        ProveQuery,
        proof_line,
        prove_ticked,
        read_ticked,
    )
    from media_hygiene.services.phone_journal import phone_run, record_pending

    runtime = runtime_of(ctx)
    output = runtime.output
    ticked, skipped = read_ticked(_stdin())
    if skipped:
        output.warning(
            ngettext(
                "{count} line of the files ticked could not be read: skipped.",
                "{count} lines of the files ticked could not be read: skipped.",
                skipped,
            ).format(count=skipped)
        )
    mapper = runtime.mapper
    folder = mapper.to_container(destination) if destination else None
    query = ProveQuery(ticked, mapper.to_container(staging), folder)
    with user_errors(output):
        if not runtime.persistent(MountKind.JOURNAL):
            raise MountError(
                _("No journal mount: nothing is deleted from the phone without one.")
            )
        journal = phone_run(runtime.locations.journal_dir, run, phone)
        proofs = prove_ticked(runtime, query)
        record_pending(journal, proofs)
    _print([f"{RUN_LINE}\t{journal.run_id}", *(proof_line(proof) for proof in proofs)])


def phone_done_command(
    ctx: typer.Context,
    *,
    run: Annotated[
        str,
        typer.Option("--run", help=_("The phone run the files were proven in.")),
    ],
) -> None:
    """Journal `done` the files gone from the phone, each proven before.

    Args:
        ctx: Typer context holding the runtime.
        run: `--run`, the phone run.
    """
    from media_hygiene.services.phone_journal import phone_run, record_done

    runtime = runtime_of(ctx)
    with user_errors(runtime.output):
        journal = phone_run(runtime.locations.journal_dir, run, "")
        done = record_done(journal, (line.strip() for line in _stdin() if line.strip()))
    _print([f"{DONE_LINE}\t{path}" for path in done])
