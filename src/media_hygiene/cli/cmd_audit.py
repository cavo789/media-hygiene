"""`media-hygiene audit`: analyse without modifying anything."""

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli import options, scan_options
from media_hygiene.cli.context import folder_layer, runtime_of, user_errors
from media_hygiene.cli.flows import audit_and_show, report_and_announce
from media_hygiene.cli.scan_options import scan_layer
from media_hygiene.console.formatting import human_size
from media_hygiene.constants import RunKind
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.report.views import ReportRecord
from media_hygiene.services.crosscheck import czkawka_command


def audit_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    prefer: Annotated[list[str] | None, options.prefer()] = None,
    protect: Annotated[list[str] | None, options.protect()] = None,
    exclude: Annotated[list[str] | None, options.exclude()] = None,
    ext: Annotated[list[str] | None, scan_options.extensions()] = None,
    exclude_name: Annotated[list[str] | None, scan_options.exclude_name()] = None,
) -> None:
    """Find exact duplicates and broken files; never writes to `/data`.

    Args:
        ctx: Typer context holding the runtime.
        prefer: `--prefer` folders.
        protect: `--protect` folders.
        exclude: `--exclude` folders.
        ext: `--ext` categories and extensions.
        exclude_name: `--exclude-name` folder names.
    """
    runtime = runtime_of(ctx)
    with user_errors(runtime.output):
        runtime = runtime.with_overrides(
            folder_layer(prefer, protect, exclude)
        ).with_overrides(scan_layer(ext, exclude_name))
        findings = audit_and_show(runtime)
        report_and_announce(runtime, ReportRecord(RunKind.AUDIT, findings))
    output, plan = runtime.output, findings.plan
    if plan.is_empty:
        output.success(_("Nothing to clean: no duplicate and no broken file."))
    else:
        output.tip(
            _("Run 'clean' (same -v options, without :ro) to free {size}.").format(
                size=human_size(plan.reclaimable),
            ),
        )
        if plan.decisions:
            output.tip(
                _(
                    "Second opinion: run Czkawka, an independent duplicate finder, on "
                    "the same folders, then 'media-hygiene crosscheck' "
                    "(same -v options):"
                ),
            )
            output.command(czkawka_command(runtime).render())
        if not runtime.settings.folders.preferred:
            output.tip(
                _(
                    "Choose which folders keep their copies: folders.preferred in "
                    "config.toml, or --prefer."
                ),
            )
    similar = findings.similar
    if similar.near_count or similar.bursts:
        output.tip(
            _(
                "Near duplicates and bursts are in the HTML report; "
                "'clean --tier near' moves near duplicates to the quarantine."
            ),
        )
    if similar.video_count:
        output.tip(
            _(
                "Re-encoded videos are in the HTML report; 'clean --tier near' moves "
                "them to the quarantine too."
            ),
        )
    if similar.bursts:
        output.tip(
            _(
                "Sort the burst series with the keyboard: 'media-hygiene review' (add "
                "-p 127.0.0.1::8080 to docker run)."
            ),
        )
    if not runtime.persistent(MountKind.CACHE):
        output.tip(
            _("Add -v media-hygiene-cache:/cache: the next audits will be much faster.")
        )
