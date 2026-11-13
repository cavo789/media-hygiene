"""The end of `sort`: what the run did, its proof, and how to undo or go on."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.config_tidy_flow import tidy_tip
from media_hygiene.cli.context import warn
from media_hygiene.cli.next_steps import carried, safety, suggest
from media_hygiene.console.incidents_view import show_failed, show_skipped
from media_hygiene.console.links_view import show_links
from media_hygiene.console.sort_view import show_kept_folders, show_manifest
from media_hygiene.console.stage_times import stages_line
from media_hygiene.console.tables import outcome_table
from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.services.next_command import CHANGING, NextVerb

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.sort_models import SortResult


def show_result(
    runtime: Runtime, result: SortResult, *, rest: str | None = None
) -> None:
    """Show what the run did, the proof, and how to undo or go on.

    Args:
        runtime: Settings, mount points and output.
        result: The run.
        rest: After a `--trial`, the command sorting the rest (`sort`, with the workbook
            named when the user named one: 0745); None otherwise.
    """
    output, host = runtime.output, runtime.mapper.to_host
    outcome = result.moves.outcome
    title = _("Sort {run_id}").format(run_id=result.run_id)
    output.show(outcome_table(outcome, title))
    show_skipped(runtime, outcome.skipped)
    show_failed(runtime, outcome.failed)
    if result.folders.removed:
        output.info(
            _("Source folders removed: {count}.").format(count=result.folders.removed)
        )
    show_kept_folders(runtime, result.folders, done=True)
    show_links(output, result.links)
    show_manifest(output, result.manifest)
    timed = stages_line(result.stages)
    if timed is not None and output.verbose:  # where the time goes, to paste
        output.info(f"[dim]{timed}[/]")
    if isinstance(result.manifest_file, MediaHygieneError):
        warn(output, result.manifest_file)
    elif result.manifest_file is not None:
        output.info(_("Manifest: {path}").format(path=host(result.manifest_file)))
    if result.moves.interrupted:
        output.warning(_("Stopped before the end, as asked."))
        output.tip(
            _("Run the same command again to continue: the files moved are skipped.")
        )
    tidy_tip(runtime)
    if rest is not None and not result.moves.interrupted:
        suggest(
            runtime,
            _("looks right? Sort the rest with the same plan:"),
            NextVerb(carried(runtime, rest), CHANGING),
        )
    safety(
        runtime,
        _(
            "Changed your mind? 'media-hygiene undo {run_id}' moves everything back:"
        ).format(run_id=result.run_id),
        NextVerb(carried(runtime, f"undo {result.run_id}"), CHANGING),
    )
