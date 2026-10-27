"""`review --intruders` in the terminal: what to pick, then what comes next (0428)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.review_next import CleanNext, tell_choices_and_clean
from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext
from media_hygiene.services.intruder_pick import intruders_set_aside
from media_hygiene.services.intruders_reviewing import (
    intruders_place,
    serve_intruders_review,
)

if TYPE_CHECKING:
    from media_hygiene.cli.review_modes import ReviewRun
    from media_hygiene.plan.models import AuditFindings


def run_intruders(run: ReviewRun, findings: AuditFindings) -> None:
    """`review --intruders`: the intruder files, per extension and per folder.

    Args:
        run: The command line, runtime, decisions file and port.
        findings: The audit just run (it counted the intruder files).
    """
    runtime = run.runtime
    output = runtime.output
    if not findings.intruders:
        output.success(_("No intruder file: nothing to pick."))
        return
    serve_intruders_review(runtime, run.port)
    picked = len(intruders_set_aside(runtime))
    output.blank()
    output.success(
        ngettext(
            "Page stopped — {count} intruder file set aside.",
            "Page stopped — {count} intruder files set aside.",
            picked,
        ).format(count=human_number(picked))
    )
    place = intruders_place(runtime)
    if not picked:
        output.info(_("Your choices are in {place}.").format(place=place.host))
        return
    text = _(
        "the same 'clean' command with {option}; the intruder files set aside go "
        "to the quarantine, 'undo' brings them back."
    )
    tell_choices_and_clean(run.ctx, runtime, CleanNext(place, text))
