"""What the console says of the local model: the work ahead, what it did, a sample."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape
from rich.table import Table

from media_hygiene.console.formatting import human_duration, human_number
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.console.output import Output
    from media_hygiene.services.classify_sample import SampleResult
    from media_hygiene.services.subject_answers import Answered
    from media_hygiene.services.subject_plan import SubjectPlan


def show_plan(output: Output, plan: SubjectPlan, model: str) -> None:
    """Say how many photos answer for how many events, and what is left to describe.

    Args:
        output: Where to print.
        plan: The plan.
        model: The vision model.
    """
    output.info(
        ngettext(
            "{units} event or lone photo has no stronger signal than its subject: "
            "{samples} photos answer for it.",
            "{units} events or lone photos have no stronger signal than their "
            "subject: {samples} photos answer for them.",
            len(plan.units),
        ).format(
            units=human_number(len(plan.units)),
            samples=human_number(plan.sample_count),
        )
    )
    if not plan.missing:
        return
    output.info(
        _("{count} of them to describe with {model}, about {duration}.").format(
            count=human_number(len(plan.missing)),
            model=escape(model),
            duration=human_duration(plan.estimate),
        )
    )


def show_answered(output: Output, answered: Answered) -> None:
    """Say what was described, and how many files each `subject` rule covers.

    Args:
        output: Where to print.
        answered: The subjects and how describing went.
    """
    outcome = answered.outcome
    if outcome.described:
        output.success(
            ngettext(
                "{count} photo described; kept in the cache.",
                "{count} photos described; kept in the cache.",
                outcome.described,
            ).format(count=human_number(outcome.described))
        )
    if outcome.unreadable:
        output.warning(
            ngettext(
                "{count} photo could not be described: unreadable, or no answer.",
                "{count} photos could not be described: unreadable, or no answer.",
                outcome.unreadable,
            ).format(count=human_number(outcome.unreadable))
        )
    if outcome.stopped:
        output.warning(
            _("Stopped: the next classify run goes on where this one stopped.")
        )
    for name, subjects in answered.subjects.items():
        output.info(
            ngettext(
                "Rule '{rule}': a subject for {count} file.",
                "Rule '{rule}': a subject for {count} files.",
                len(subjects),
            ).format(rule=escape(name), count=human_number(len(subjects)))
        )


def show_sample(
    output: Output, result: SampleResult, host: Callable[[Path], str]
) -> None:
    """Print the sample, its cost per photo and the estimate of a full run.

    Args:
        output: Where to print.
        result: The sample.
        host: Container path → host path.
    """
    if not result.rows:
        output.info(_("No photo left to describe: every candidate is in the cache."))
        return
    table = Table(_("Photo"), _("Description"), _("Category"), expand=True)
    for row in result.rows:
        table.add_row(
            escape(host(row.path)), escape(row.description), escape(row.category)
        )
    output.show(table)
    output.info(
        _("Per photo: {describe:.1f} s to describe, {map:.1f} s to map.").format(
            describe=result.describe_seconds, map=result.map_seconds
        )
    )
    output.info(
        _("A full run would describe {count} more photos: about {duration}.").format(
            count=human_number(result.to_describe),
            duration=human_duration(result.total),
        )
    )
    output.tip(_("Nothing is proposed by --sample: run classify without it."))
