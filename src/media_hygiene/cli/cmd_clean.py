"""`media-hygiene clean`: duplicates to the quarantine, journaled and undoable."""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

from media_hygiene.cli import clean_options, folder_options, options, scan_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.cli.folder_options import FolderOptions
from media_hygiene.cli.scan_options import scan_layer
from media_hygiene.constants import CleanTier, ExitCode, RunKind
from media_hygiene.i18n import _
from media_hygiene.report.clean_done import CleanAsked

if TYPE_CHECKING:
    from media_hygiene.actions.outcome import Outcome
    from media_hygiene.services.runtime import Runtime


# The options are parameters (and locals): the documented exception for Typer commands.
def clean_command(  # pylint: disable=too-many-arguments,too-many-locals
    ctx: typer.Context,
    *,
    tier: Annotated[CleanTier, clean_options.tier()] = CleanTier.EXACT,
    decisions: Annotated[Path | None, clean_options.decisions()] = None,
    yes: Annotated[bool, options.yes()] = False,
    delete: Annotated[bool, clean_options.delete()] = False,
    prefer: Annotated[list[str] | None, folder_options.prefer()] = None,
    protect: Annotated[list[str] | None, folder_options.protect()] = None,
    exclude: Annotated[list[str] | None, folder_options.exclude()] = None,
    backup: Annotated[list[str] | None, folder_options.backup()] = None,
    ext: Annotated[list[str] | None, scan_options.extensions()] = None,
    exclude_name: Annotated[list[str] | None, scan_options.exclude_name()] = None,
) -> None:
    """Audit, confirm, then set duplicate copies aside and handle broken files.

    Args:
        ctx: Typer context holding the runtime.
        prefer: `--prefer` folders.
        protect: `--protect` folders.
        exclude: `--exclude` folders.
        backup: `--backup` folders, compared and never changed.
        ext: `--ext` categories and extensions.
        exclude_name: `--exclude-name` folder names.
        yes: `--yes`, skip the confirmation.
        tier: `--tier`, near duplicates are moved to the quarantine too: the sure
            groups (`near`) or every group (`near-all`).
        decisions: `--decisions`, the review downloaded from a report or written by
            `review`.
        delete: `--delete`, exact copies are deleted for good, not moved.

    Raises:
        typer.Exit: The user declined.
    """
    from media_hygiene.cli.clean_confirm import confirm_clean
    from media_hygiene.cli.flows import (
        audit_and_show,
        report_and_announce,
        show_pairs,
        show_second_opinion,
    )
    from media_hygiene.cli.near_preview import near_waiting, show_near_first
    from media_hygiene.console.emptied_view import show_clean_outcome, tell_emptied
    from media_hygiene.console.progress import RichProgress
    from media_hygiene.plan.near_review import NearSelection
    from media_hygiene.report.views import ReportRecord
    from media_hygiene.services.clean import CleanMode, CleanService
    from media_hygiene.services.decisions_archive import archive_decisions
    from media_hygiene.services.emptied_folders import emptied_by
    from media_hygiene.services.near_tier import NearRequest, near_verdicts, with_near
    from media_hygiene.services.review import apply_review, load_review, review_choices

    runtime = runtime_of(ctx)
    output = runtime.output
    if decisions is not None and _already_applied(runtime, decisions, tier):
        return
    with user_errors(output), RichProgress(output.console) as progress:
        runtime = runtime.with_overrides(
            FolderOptions(prefer, protect, exclude, backup).layer()
        ).with_overrides(scan_layer(ext, exclude_name))
        service = CleanService(runtime, progress)
        review = load_review(runtime, decisions) if decisions else None
        bursts = review is not None and (
            bool(review.chosen)
            or any(b.discarded for b in review.bursts)
            or any(entry.aside for entry in review.unwanted)
        )
        service.ensure_ready(CleanMode(tier is not CleanTier.EXACT, bursts, delete))
        findings = audit_and_show(runtime)
        plan = service.feasible(replace(findings.plan, delete_copies=delete))
        if tier is not CleanTier.EXACT:
            verdicts = near_verdicts(runtime, findings, review.near) if review else None
            selection = NearSelection(tier is CleanTier.NEAR_ALL, verdicts)
            plan = with_near(runtime, plan, NearRequest(findings, selection))
        elif review is not None and review.near:
            output.info(near_waiting(len(review.near)))
        if review is not None:
            choices = review_choices(runtime, findings, review)
            plan = apply_review(runtime, plan, choices)
            show_pairs(runtime, replace(findings, plan=plan))
        verdict = None if plan.is_empty else show_second_opinion(runtime, findings)
        if plan.is_empty:
            output.success(_("Nothing to clean: no duplicate and no broken file."))
            return
        tell_emptied(output, emptied_by(runtime, plan).predicted())
        show_near_first(runtime, replace(findings, plan=plan), yes=yes)  # last: a link
        if not confirm_clean(runtime, plan, yes):
            output.drop_advice()
            output.info(_("Nothing was changed."))
            raise typer.Exit(ExitCode.OK)
        output.title(_("Clean"))
        run_id, outcome = service.execute(plan)
        show_clean_outcome(output, outcome, _("Clean {run_id}").format(run_id=run_id))
        report_and_announce(
            runtime,
            ReportRecord(
                RunKind.CLEAN,
                replace(findings, plan=plan),
                outcome,
                run_id,
                crosscheck=verdict,
                asked=CleanAsked(tier is not CleanTier.EXACT, bursts),
            ),
        )
    _after_clean_tips(runtime, run_id, outcome)
    if decisions is not None:
        archive_decisions(runtime, decisions, run_id)


def _already_applied(runtime: Runtime, decisions: Path, tier: CleanTier) -> bool:
    """Say the decisions were applied already, and that a review makes new ones.

    Args:
        runtime: Settings, mount points and output.
        decisions: `--decisions` value.
        tier: `--tier`: near duplicates are decided with `review --near`.

    Returns:
        True when a clean applied them: the file is gone, its archive is there.
    """
    from media_hygiene.cli.next_steps import carried, suggest
    from media_hygiene.services.decisions_archive import applied_before, tell_applied
    from media_hygiene.services.next_command import NextVerb

    archive = applied_before(runtime, decisions)
    if archive is None:
        return False
    tell_applied(runtime, archive)
    verb = "review" if tier is CleanTier.EXACT else "review --near"
    text = _("new choices first: '{verb}' writes a new decisions file.")
    port = runtime.settings.review.port
    suggest(
        runtime, text.format(verb=verb), NextVerb(carried(runtime, verb), port=port)
    )
    return True


def _after_clean_tips(runtime: Runtime, run_id: str, outcome: Outcome) -> None:
    """Tell how to undo the clean, and that `purge` frees the space.

    Args:
        runtime: Settings, mount points and output.
        run_id: The clean run.
        outcome: What the clean did.
    """
    from media_hygiene.cli.next_steps import carried, safety, suggest
    from media_hygiene.services.next_command import CHANGING, NextVerb

    safety(
        runtime,
        _(
            "Changed your mind? 'media-hygiene undo {run_id}' restores everything:"
        ).format(run_id=run_id),
        NextVerb(carried(runtime, f"undo {run_id}"), CHANGING),
    )
    if outcome.quarantined:
        suggest(
            runtime,
            _("once you have checked, 'purge' frees the space of the files set aside."),
            NextVerb(carried(runtime, f"purge {run_id}"), CHANGING),
        )
