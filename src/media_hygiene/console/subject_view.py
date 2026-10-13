"""What the console says of the local model: the work ahead, what it did, a sample."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape
from rich.table import Table

from media_hygiene.console.describe_view import show_describe_counts
from media_hygiene.console.formatting import human_duration, human_number
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.console.output import Output
    from media_hygiene.services.classify_sample import SampleResult
    from media_hygiene.services.subject_answers import Answered
    from media_hygiene.services.subject_plan import SubjectPlan


def show_plan(output: Output, plan: SubjectPlan) -> None:
    """Say how many groups the model answers for, and by how many photos.

    Args:
        output: Where to print.
        plan: The plan.
    """
    groups = ngettext(
        "{units} group of photos (an event or a lone photo) no rule of yours took:",
        "{units} groups of photos (events or lone photos) no rule of yours took:",
        len(plan.units),
    ).format(units=human_number(len(plan.units)))
    samples = human_number(plan.sample_count)
    if plan.per_event:
        looked = _(
            "the model will look at {samples} of them "
            "(up to {per_event} per event, the others follow)."
        ).format(samples=samples, per_event=human_number(plan.per_event))
    else:
        looked = _("the model will look at each of their {samples} photos.").format(
            samples=samples
        )
    output.info(f"{groups} {looked}")


def show_work(output: Output, plan: SubjectPlan, model: str) -> None:
    """Say how many samples the model will describe, and how long it should take.

    Args:
        output: Where to print.
        plan: The plan.
        model: The vision model.
    """
    if not plan.missing:
        return
    work = {
        "count": human_number(len(plan.missing)),
        "model": escape(model),
        "duration": human_duration(plan.estimate),
        "cached": human_number(plan.cached),
    }
    if plan.cached:
        line = _(
            "{count} to describe with {model} ({cached} already in the cache), "
            "about {duration}."
        )
    else:
        line = _("{count} to describe with {model}, about {duration}.")
    output.info(line.format(**work))


def show_not_described(output: Output, plan: SubjectPlan) -> None:
    """`--no-describe`: say what stays undescribed, and that it costs nothing.

    Args:
        output: Where to print.
        plan: The plan.
    """
    if not plan.missing:
        return
    output.info(
        ngettext(
            "{count} sample not described yet (--no-describe): only those already "
            "described answer, in a few seconds.",
            "{count} samples not described yet (--no-describe): only those already "
            "described answer, in a few seconds.",
            len(plan.missing),
        ).format(count=human_number(len(plan.missing)))
    )


def show_answered(output: Output, answered: Answered) -> None:
    """Say what was described, the files each `subject` rule sorts, the groups left.

    Args:
        output: Where to print.
        answered: The subjects and how describing went.
    """
    outcome = answered.outcome
    show_describe_counts(output, outcome)
    if outcome.stopped:
        output.warning(
            _("Stopped: the next classify run goes on where this one stopped.")
        )
    for name, subjects in answered.subjects.items():
        line = ngettext(
            "Rule '{rule}': {count} file sorted by what the model saw",
            "Rule '{rule}': {count} files sorted by what the model saw",
            len(subjects),
        ).format(rule=escape(name), count=human_number(len(subjects)))
        left = answered.unanswered.get(name, 0)
        if left:
            line += ngettext(
                "; {groups} group without a subject → your other rules, else {band}.",
                "; {groups} groups without a subject → your other rules, else {band}.",
                left,
            ).format(groups=human_number(left), band=_("To sort"))
        else:
            line += "."
        output.info(line)


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
