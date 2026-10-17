"""`media-hygiene crosscheck`: compare a fresh audit with Czkawka's results."""

# pylint: disable=import-outside-toplevel,too-many-locals  # lazy: a command imports
# the code it runs when it runs; those imports count as local variables.

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli import crosscheck_options, folder_options, scan_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.cli.folder_options import FolderOptions
from media_hygiene.cli.scan_options import scan_layer
from media_hygiene.constants import ExitCode, RunKind
from media_hygiene.i18n import _


def crosscheck_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    prefer: Annotated[list[str] | None, folder_options.prefer()] = None,
    protect: Annotated[list[str] | None, folder_options.protect()] = None,
    exclude: Annotated[list[str] | None, folder_options.exclude()] = None,
    backup: Annotated[list[str] | None, folder_options.backup()] = None,
    ext: Annotated[list[str] | None, scan_options.extensions()] = None,
    exclude_name: Annotated[list[str] | None, scan_options.exclude_name()] = None,
    fresh: Annotated[bool, crosscheck_options.fresh()] = False,
    print_command: Annotated[bool, crosscheck_options.print_command()] = False,
) -> None:
    """Audit again (fast with the cache), run Czkawka, then compare its groups.

    Args:
        ctx: Typer context holding the runtime.
        prefer: `--prefer` folders.
        protect: `--protect` folders.
        exclude: `--exclude` folders.
        backup: `--backup` folders, compared and never changed.
        ext: `--ext` categories and extensions.
        exclude_name: `--exclude-name` folder names.
        fresh: `--fresh`, Czkawka ignores its cache.
        print_command: `--print-command`, Czkawka is run by the user.

    Raises:
        MountError: No reports mount point, where Czkawka's results are kept.
        typer.Exit: Czkawka has not been run yet (`--print-command`, or outside
            the image).
    """
    from media_hygiene.cli.czkawka_flow import run_second_opinion
    from media_hygiene.cli.flows import (
        audit_and_show,
        report_and_announce,
        show_verdict,
    )
    from media_hygiene.errors import MountError
    from media_hygiene.paths.mount_kind import MountKind
    from media_hygiene.report.views import ReportRecord
    from media_hygiene.services.crosscheck import (
        cross_check,
        czkawka_command,
        czkawka_run,
    )

    runtime = runtime_of(ctx)
    output = runtime.output
    with user_errors(output):
        if not runtime.persistent(MountKind.REPORTS):
            raise MountError(
                _("'crosscheck' keeps Czkawka's results in /reports: mount it."),
                _('Add -v "<a folder of yours>:/reports".'),
            )
        runtime = runtime.with_overrides(
            FolderOptions(prefer, protect, exclude, backup).layer()
        ).with_overrides(scan_layer(ext, exclude_name))
        findings = audit_and_show(runtime)
        run = None if print_command else czkawka_run(runtime, fresh=fresh)
        if run is not None:
            run_second_opinion(runtime, run)
        result = cross_check(runtime, findings)
        if result is None:
            output.error(_("No Czkawka results yet: run Czkawka first (PowerShell):"))
            output.command(czkawka_command(runtime).render())
            raise typer.Exit(ExitCode.FAILURE)
        output.title(_("Second opinion"))
        verdict = show_verdict(runtime, result)
        report_and_announce(
            runtime, ReportRecord(RunKind.AUDIT, findings, crosscheck=verdict)
        )
