"""What `tags` says of search by meaning: the work, the download, the end."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_duration, human_number
from media_hygiene.i18n import _, ngettext
from media_hygiene.meaning.clip import DOWNLOAD_MB

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.services.meaning import MeaningOutcome, MeaningWork


def show_meaning_work(output: Output, work: MeaningWork) -> None:
    """Say how many photos the model will look at, and how long it should take.

    Args:
        output: Where to print.
        work: The photos without a vector.
    """
    if not work.missing:
        output.info(_("Search by meaning: every photo is looked at already."))
        return
    output.info(
        ngettext(
            "Search by meaning: {count} photo to look at on this computer's "
            "processor, about {duration}. Ctrl+C stops; what is done is kept.",
            "Search by meaning: {count} photos to look at on this computer's "
            "processor, about {duration}. Ctrl+C stops; what is done is kept.",
            len(work.missing),
        ).format(
            count=human_number(len(work.missing)),
            duration=human_duration(work.estimate),
        )
    )


def show_meaning_download(output: Output) -> None:
    """Say, before it starts, that the model is downloaded and how large it is.

    Args:
        output: Where to print.
    """
    output.info(
        _(
            "Downloading the model of search by meaning into the cache, once "
            "({size} MB): it runs on this computer, nothing about your photos is sent."
        ).format(size=human_number(DOWNLOAD_MB))
    )


def show_meaning_done(output: Output, outcome: MeaningOutcome) -> None:
    """Say how many photos can now be found by what they show.

    Args:
        output: Where to print.
        outcome: How the run went.
    """
    output.success(
        ngettext(
            "{count} photo can now be found by what it shows ({duration}).",
            "{count} photos can now be found by what they show ({duration}).",
            outcome.seen,
        ).format(
            count=human_number(outcome.seen),
            duration=human_duration(outcome.seconds),
        )
    )
    if outcome.unreadable:
        output.warning(
            ngettext(
                "{count} photo could not be decoded: it has no vector.",
                "{count} photos could not be decoded: they have no vector.",
                outcome.unreadable,
            ).format(count=human_number(outcome.unreadable))
        )
    if outcome.stopped:
        output.warning(_("Stopped: the next tags run goes on where this one stopped."))
