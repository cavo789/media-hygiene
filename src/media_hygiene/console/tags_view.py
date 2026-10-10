"""What the console says of `tags`: the cheap words, the work ahead, what was done."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape
from rich.table import Table

from media_hygiene.console.formatting import human_duration, human_number
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.classify.ai.describe import DescribeOutcome
    from media_hygiene.console.output import Output
    from media_hygiene.services.tag_describe import TagSample
    from media_hygiene.services.tag_work import TagWork


def show_cheap(output: Output, work: TagWork, written: int) -> None:
    """Say how many words the folders, dates and places gave.

    Args:
        output: Where to print.
        work: The files of the run.
        written: How many tags were written.
    """
    output.success(
        ngettext(
            "{count} file: {words} words from its folders, date and place.",
            "{count} files: {words} words from their folders, dates and places.",
            len(work.files),
        ).format(count=human_number(len(work.files)), words=human_number(written))
    )


def show_work(output: Output, work: TagWork, model: str) -> None:
    """Say how many photos the model has still to describe, and how long it takes.

    Args:
        output: Where to print.
        work: The work of the run.
        model: The vision model.
    """
    if not work.missing:
        return
    output.info(
        _(
            "{count} photos to describe with {model}, about {duration}: one per set "
            "of identical files and per burst series."
        ).format(
            count=human_number(len(work.missing)),
            model=escape(model),
            duration=human_duration(work.estimate),
        )
    )


def show_described(output: Output, outcome: DescribeOutcome) -> None:
    """Say what the model described, could not describe, or why it stopped.

    Args:
        output: Where to print.
        outcome: How describing went.
    """
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
        output.warning(_("Stopped: the next tags run goes on where this one stopped."))


def show_vision(output: Output, work: TagWork, tagged: int) -> None:
    """Say how many photos have the model's words, and how many are left.

    Args:
        output: Where to print.
        work: The photos the model may see.
        tagged: How many have its words.
    """
    left = len(work.vision.answered_by) - tagged
    output.info(
        ngettext(
            "{count} photo has the words of the vision model; {left} left.",
            "{count} photos have the words of the vision model; {left} left.",
            tagged,
        ).format(count=human_number(tagged), left=human_number(left))
    )


def show_tag_sample(
    output: Output, sample: TagSample, host: Callable[[Path], str]
) -> None:
    """Print the sample, the time per photo and the estimate of a full run.

    Args:
        output: Where to print.
        sample: The sample.
        host: Container path → host path.
    """
    if not sample.rows:
        output.info(_("No photo left to describe: every one is in the cache."))
        return
    table = Table(_("Photo"), _("Description"), _("Tags"), _("Seconds"), expand=True)
    for row in sample.rows:
        table.add_row(
            escape(host(row.path)),
            escape(row.sentence),
            escape(", ".join(row.tags)),
            f"{row.seconds:.1f}",
        )
    output.show(table)
    output.info(
        _("A full run would describe {count} more photos: about {duration}.").format(
            count=human_number(sample.to_describe),
            duration=human_duration(sample.total),
        )
    )
