"""What `tags` says of search by meaning: the work, the download, the end."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from rich.markup import escape

from media_hygiene.console.formatting import human_duration, human_number
from media_hygiene.i18n import _, ngettext
from media_hygiene.meaning.clip import DOWNLOAD_MB

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.services.meaning import MeaningOutcome, MeaningWork


# Enough to look at them; more is a damaged folder, not a list to read in a console.
_NAMED: Final = 20


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


def left_aside_lines(
    outcome: MeaningOutcome, mapper: HostPathMapper
) -> tuple[str, ...]:
    """Say which photos got no vector, by name: a count leaves nothing to act on.

    Args:
        outcome: How the run went.
        mapper: Shows each path as on the host.

    Returns:
        The lines, none when every photo was looked at.
    """
    lines: list[str] = []
    bad = outcome.unreadable
    if bad:
        lines.append(
            ngettext(
                "{count} photo could not be decoded: it has no vector.",
                "{count} photos could not be decoded: they have no vector.",
                len(bad),
            ).format(count=human_number(len(bad)))
        )
        lines.extend(f"  {mapper.to_host(path)}" for path in bad[:_NAMED])
    if len(bad) > _NAMED:
        lines.append(
            _("  … and {count} more.").format(count=human_number(len(bad) - _NAMED))
        )
    if outcome.absent:
        lines.append(
            ngettext(
                "{count} photo the audit listed is not there: deleted since, or "
                "its drive is not mounted.",
                "{count} photos the audit listed are not there: deleted since, or "
                "their drive is not mounted.",
                outcome.absent,
            ).format(count=human_number(outcome.absent))
        )
    return tuple(lines)


def show_meaning_done(
    output: Output, outcome: MeaningOutcome, mapper: HostPathMapper
) -> None:
    """Say how many photos can now be found by what they show.

    Args:
        output: Where to print.
        outcome: How the run went.
        mapper: Shows each path as on the host.
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
    for line in left_aside_lines(outcome, mapper):
        output.warning(escape(line))
    if outcome.stopped:
        output.warning(_("Stopped: the next tags run goes on where this one stopped."))
