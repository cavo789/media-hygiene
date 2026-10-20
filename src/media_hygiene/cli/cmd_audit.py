"""`media-hygiene audit`: analyse without modifying anything."""

# pylint: disable=import-outside-toplevel,too-many-locals  # lazy: a command imports
# the code it runs when it runs; those imports count as local variables.

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import typer

from media_hygiene.cli import folder_options, options, scan_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.cli.folder_options import FolderOptions
from media_hygiene.cli.scan_options import scan_layer
from media_hygiene.constants import RunKind
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.services.runtime import Runtime


def audit_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    *,
    prefer: Annotated[list[str] | None, folder_options.prefer()] = None,
    protect: Annotated[list[str] | None, folder_options.protect()] = None,
    exclude: Annotated[list[str] | None, folder_options.exclude()] = None,
    backup: Annotated[list[str] | None, folder_options.backup()] = None,
    ext: Annotated[list[str] | None, scan_options.extensions()] = None,
    exclude_name: Annotated[list[str] | None, scan_options.exclude_name()] = None,
    full: Annotated[
        bool,
        typer.Option(
            "--full",
            rich_help_panel=options.panel_advanced(),
            help=_(
                "Read every folder again, even those that did not change since the "
                "last audit: for a photo changed in place by another program."
            ),
        ),
    ] = False,
    people: Annotated[
        bool,
        typer.Option(
            "--people",
            rich_help_panel=options.panel_advanced(),
            help=_(
                "Then look for faces in the photos not looked at yet (as 'people' "
                "does), after saying how long it takes and asking."
            ),
        ),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            rich_help_panel=options.panel_advanced(),
            help=_("With --people: do not ask, go on."),
        ),
    ] = False,
) -> None:
    """Find exact duplicates and broken files; never writes to `/data`.

    Args:
        ctx: Typer context holding the runtime.
        prefer: `--prefer` folders.
        protect: `--protect` folders.
        exclude: `--exclude` folders.
        backup: `--backup` folders, compared and never changed.
        ext: `--ext` categories and extensions.
        exclude_name: `--exclude-name` folder names.
        full: `--full`, no folder taken from the index.
        people: `--people`, faces after the audit.
        yes: `--yes`, no question before the faces.
    """
    from media_hygiene.cli.audit_actions import second_opinion, show_actions
    from media_hygiene.cli.audit_people import audit_people
    from media_hygiene.cli.audit_tips import setup_tips
    from media_hygiene.cli.flows import audit_and_show, report_and_announce
    from media_hygiene.console.advice import Advice, TipKind
    from media_hygiene.report.views import ReportRecord

    runtime = runtime_of(ctx)
    with user_errors(runtime.output):
        runtime = runtime.with_overrides(
            FolderOptions(prefer, protect, exclude, backup).layer()
        ).with_overrides(scan_layer(ext, exclude_name))
        if full:
            runtime = runtime.with_overrides({"scan": {"full_check_days": 0}})
        findings = audit_and_show(runtime)
        actions = show_actions(ctx, runtime, findings)
        report_and_announce(
            runtime, ReportRecord(RunKind.AUDIT, findings, actions=actions)
        )
    output, plan = runtime.output, findings.plan
    if plan.is_empty:
        output.success(_("Nothing to clean: no duplicate and no broken file."))
    elif plan.decisions and not runtime.settings.folders.preferred:
        output.advise(
            Advice(
                TipKind.NEXT,  # changes what clean keeps: before the setup line
                _(
                    "Choose which folders keep their copies: folders.preferred in "
                    "config.toml, or --prefer."
                ),
            )
        )
    similar = findings.similar
    if similar.near_count or similar.bursts:
        output.advise(
            Advice(
                TipKind.DISCOVERY,
                _(
                    "Near duplicates and bursts are in the HTML report; "
                    "'clean --tier near' moves the sure near duplicates to the "
                    "quarantine, 'review --near' decides those to check."
                ),
            )
        )
    if similar.video_count:
        output.advise(
            Advice(
                TipKind.DISCOVERY,
                _(
                    "Re-encoded videos are in the HTML report; 'clean --tier near' "
                    "moves the sure ones to the quarantine too."
                ),
            )
        )
    if people or runtime.settings.people.with_audit:
        with user_errors(output):
            audit_people(runtime, yes)
    second_opinion(runtime, plan)
    setup_tips(runtime)
    _next_step(ctx, runtime, findings)


def _next_step(ctx: typer.Context, runtime: Runtime, findings: AuditFindings) -> None:
    """Close with the step that logically follows: the copies first, then the bursts.

    Args:
        ctx: Typer context of the audit, whose options the next command keeps.
        runtime: Settings, mount points and output.
        findings: What the audit found.
    """
    from media_hygiene.cli.next_steps import carried, suggest
    from media_hygiene.console.formatting import human_size
    from media_hygiene.services.next_command import CHANGING, NextVerb

    plan = findings.plan
    if plan.decisions:
        suggest(
            runtime,
            _("run 'clean' to set {size} of copies aside.").format(
                size=human_size(plan.reclaimable)
            ),
            NextVerb(carried(runtime, "clean", ctx), CHANGING),
        )
    elif findings.similar.bursts:
        suggest(
            runtime,
            _("sort the burst series with the keyboard, in 'review'."),
            NextVerb(
                carried(runtime, "review", ctx), port=runtime.settings.review.port
            ),
        )
