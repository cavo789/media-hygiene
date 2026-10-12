"""What the console says of `people`: the work, the faces found, the groups."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.console.formatting import human_duration, human_number
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.console.output import Output
    from media_hygiene.index.face_rows import FaceTally
    from media_hygiene.services.people_find import FindOutcome
    from media_hygiene.services.people_groups import PeopleGroups

_LARGEST: Final = 5  # group sizes listed
_DECIMALS: Final = 2  # of the seconds per photo


def show_privacy(output: Output) -> None:
    """Say, in one line, where the faces stay and how to delete them.

    Args:
        output: Where to print.
    """
    output.info(
        _(
            "🔒 Faces are personal data: they stay in the cache (/cache), nothing is "
            "sent anywhere. 'people --forget' deletes them all."
        )
    )


def show_absent(output: Output, absent: int) -> None:
    """Say how many photos of the index are not on disk, and why it is harmless.

    Args:
        output: Where to print.
        absent: Photos of the index missing from the mounted folders.
    """
    if absent:
        output.info(
            ngettext(
                "{count} photo of the index is not in the mounted folders: left "
                "aside. Mount its folder to look at it too.",
                "{count} photos of the index are not in the mounted folders: left "
                "aside. Mount their folders to look at them too.",
                absent,
            ).format(count=human_number(absent))
        )


def show_missing(output: Output, missing: int, total: int) -> None:
    """Say how many photos are still to analyse.

    Args:
        output: Where to print.
        missing: Photos not analysed yet.
        total: Photos of the run.
    """
    if not missing:
        return
    output.info(
        ngettext(
            "{count} photo of {total} to analyse; the next runs analyse new ones only.",
            "{count} photos of {total} to analyse; the next runs analyse new ones "
            "only.",
            missing,
        ).format(count=human_number(missing), total=human_number(total))
    )


def show_found(output: Output, outcome: FindOutcome) -> None:
    """Say how many photos were analysed and faces found, or why it stopped.

    Args:
        output: Where to print.
        outcome: How finding went.
    """
    if outcome.analysed:
        output.success(
            ngettext(
                "{count} photo analysed: {faces} faces, {seconds} s per photo.",
                "{count} photos analysed: {faces} faces, {seconds} s per photo.",
                outcome.analysed,
            ).format(
                count=human_number(outcome.analysed),
                faces=human_number(outcome.faces),
                seconds=human_number(outcome.seconds / outcome.analysed, _DECIMALS),
            )
        )
    if outcome.unreadable:
        output.warning(
            ngettext(
                "{count} photo could not be decoded.",
                "{count} photos could not be decoded.",
                outcome.unreadable,
            ).format(count=human_number(outcome.unreadable))
        )
    if outcome.stopped:
        output.warning(
            _("Stopped: the next people run goes on where this one stopped.")
        )


def show_estimate(output: Output, left: int, seconds: float) -> None:
    """After `--sample`: what analysing the other photos would take.

    Args:
        output: Where to print.
        left: Photos still not analysed.
        seconds: The estimated time.
    """
    if left:
        output.info(
            _("A full run would analyse {count} more photos: about {duration}.").format(
                count=human_number(left), duration=human_duration(seconds)
            )
        )
    else:
        output.info(_("No photo left to analyse: every one is in the cache."))
    output.info(
        _(
            "--sample only measures: no page opens. Run people without it to see "
            "the faces in your browser."
        )
    )


def show_groups(
    output: Output, groups: PeopleGroups, context: tuple[FaceTally, PeopleSettings]
) -> None:
    """Say how the faces of the index group, and which ones were left out.

    Args:
        output: Where to print.
        groups: The groups.
        context: What the index holds, and the settings of `[people]`.
    """
    tally, settings = context
    people = groups.people
    sizes = ", ".join(human_number(len(group)) for group in people[:_LARGEST])
    counts = {"faces": human_number(tally.faces), "photos": human_number(tally.photos)}
    if not people:
        output.info(
            _(
                "{faces} faces in {photos} photos: no two of them look alike enough "
                "to be grouped."
            ).format(**counts)
        )
    else:
        output.success(
            ngettext(
                "{faces} faces in {photos} photos: {count} group of faces alike "
                "({sizes}), {alone} seen once.",
                "{faces} faces in {photos} photos: {count} groups of faces alike, the "
                "largest {sizes}; {alone} seen once.",
                len(people),
            ).format(
                **counts,
                count=human_number(len(people)),
                sizes=sizes,
                alone=human_number(groups.alone),
            )
        )
    if groups.too_small or groups.too_blurry:
        output.info(
            _(
                "Left out: {small} faces smaller than {pixels} pixels, {blurry} "
                "blurrier than {sharpness}."
            ).format(
                small=human_number(groups.too_small),
                pixels=settings.min_face,
                blurry=human_number(groups.too_blurry),
                sharpness=human_number(
                    settings.min_sharpness,
                    0 if settings.min_sharpness.is_integer() else 1,
                ),
            )
        )


def show_named(output: Output, named: Sequence[tuple[str, int]]) -> None:
    """List the people named and their photos, then point at the page for the rest.

    Args:
        output: Where to print.
        named: Each person and their photos of this run, most first.
    """
    if not named:
        return
    listed = ", ".join(
        _("{name}: {count} photos").format(name=name, count=human_number(count))
        for name, count in named
    )
    output.success(_("Named: {people}.").format(people=listed))
