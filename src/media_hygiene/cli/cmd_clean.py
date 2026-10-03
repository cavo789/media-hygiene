"""`media-hygiene clean`: duplicates to the quarantine, journaled and undoable."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

from media_hygiene.cli import clean_options, options, scan_options
from media_hygiene.cli.clean_confirm import confirm_clean
from media_hygiene.cli.context import folder_layer, runtime_of, user_errors
from media_hygiene.cli.flows import (
    audit_and_show,
    report_and_announce,
    show_pairs,
    show_second_opinion,
)
from media_hygiene.cli.scan_options import scan_layer
from media_hygiene.console.progress import RichProgress
from media_hygiene.console.tables import outcome_table
from media_hygiene.constants import CleanTier, ExitCode, RunKind
from media_hygiene.i18n import _
from media_hygiene.report.views import ReportRecord
from media_hygiene.services.clean import CleanMode, CleanService
from media_hygiene.services.review import apply_review, load_review, review_choices

if TYPE_CHECKING:
    from media_hygiene.actions.outcome import Outcome
    from media_hygiene.console.output import Output


# The options are parameters (and locals): the documented exception for Typer commands.
def clean_command(  # pylint: disable=too-many-arguments,too-many-locals
    ctx: typer.Context,
    *,
    prefer: Annotated[list[str] | None, options.prefer()] = None,
    protect: Annotated[list[str] | None, options.protect()] = None,
    exclude: Annotated[list[str] | None, options.exclude()] = None,
    ext: Annotated[list[str] | None, scan_options.extensions()] = None,
    exclude_name: Annotated[list[str] | None, scan_options.exclude_name()] = None,
    yes: Annotated[bool, options.yes()] = False,
    tier: Annotated[CleanTier, clean_options.tier()] = CleanTier.EXACT,
    decisions: Annotated[Path | None, clean_options.decisions()] = None,
    delete: Annotated[bool, clean_options.delete()] = False,
) -> None:
    """Audit, confirm, then set duplicate copies aside and handle broken files.

    Args:
        ctx: Typer context holding the runtime.
        prefer: `--prefer` folders.
        protect: `--protect` folders.
        exclude: `--exclude` folders.
        ext: `--ext` categories and extensions.
        exclude_name: `--exclude-name` folder names.
        yes: `--yes`, skip the confirmation.
        tier: `--tier`, near duplicates are moved to the quarantine too.
        decisions: `--decisions`, the review downloaded from a report or written by
            `review`.
        delete: `--delete`, exact copies are deleted for good, not moved.

    Raises:
        typer.Exit: The user declined.
    """
    runtime = runtime_of(ctx)
    output = runtime.output
    with user_errors(output), RichProgress(output.console) as progress:
        runtime = runtime.with_overrides(
            folder_layer(prefer, protect, exclude)
        ).with_overrides(scan_layer(ext, exclude_name))
        service = CleanService(runtime, progress)
        review = load_review(runtime, decisions) if decisions else None
        bursts = review is not None and bool(review.bursts)
        service.ensure_ready(CleanMode(tier is CleanTier.NEAR, bursts, delete))
        findings = audit_and_show(runtime)
        plan = service.feasible(replace(findings.plan, delete_copies=delete))
        if tier is CleanTier.NEAR:
            plan = service.with_near(plan, findings)
        if review is not None:
            choices = review_choices(runtime, findings, review)
            plan = apply_review(runtime, plan, choices)
            show_pairs(runtime, replace(findings, plan=plan))
        verdict = None if plan.is_empty else show_second_opinion(runtime, findings)
        if plan.is_empty:
            output.success(_("Nothing to clean: no duplicate and no broken file."))
            return
        if not confirm_clean(runtime, plan, yes):
            output.info(_("Nothing was changed."))
            raise typer.Exit(ExitCode.OK)
        output.title(_("Clean"))
        run_id, outcome = service.execute(plan)
        output.show(outcome_table(outcome, _("Clean {run_id}").format(run_id=run_id)))
        report_and_announce(
            runtime,
            ReportRecord(
                RunKind.CLEAN,
                replace(findings, plan=plan),
                outcome,
                run_id,
                crosscheck=verdict,
            ),
        )
    _after_clean_tips(output, run_id, outcome)


def _after_clean_tips(output: Output, run_id: str, outcome: Outcome) -> None:
    """Tell how to undo the clean, and that `purge` frees the space.

    Args:
        output: Where to print.
        run_id: The clean run.
        outcome: What the clean did.
    """
    undo_tip = _(
        "Changed your mind? 'media-hygiene undo {run_id}' restores everything."
    )
    output.tip(undo_tip.format(run_id=run_id))
    if outcome.quarantined:
        purge_tip = _(
            "The space is freed by 'purge', once you have checked: "
            "media-hygiene purge {run_id}"
        )
        output.tip(purge_tip.format(run_id=run_id))
