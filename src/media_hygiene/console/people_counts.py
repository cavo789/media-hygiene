"""What the console says of the photos a `people` run analyses (0803).

The photos never analysed and those analysed before whose turn is still to guess (0803)
or whose faces further away are still to add (0841) are counted apart: the second are
no new photos.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import ngettext

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.services.people import PeopleWork


def show_missing(output: Output, work: PeopleWork) -> None:
    """Say how many photos are still to analyse, and how many to look at again.

    Args:
        output: Where to print.
        work: The photos of the run.
    """
    total = human_number(len(work.photos))
    if work.new:
        output.info(
            ngettext(
                "{count} photo of {total} to analyse; the next runs analyse new ones "
                "only.",
                "{count} photos of {total} to analyse; the next runs analyse new ones "
                "only.",
                work.new,
            ).format(count=human_number(work.new), total=total)
        )
    if work.turn_only:
        output.info(
            ngettext(
                "{count} photo of {total} to look at again (analysed before, not "
                "new): its turn, or faces further away.",
                "{count} photos of {total} to look at again (analysed before, not "
                "new): their turn, or faces further away.",
                work.turn_only,
            ).format(count=human_number(work.turn_only), total=total)
        )
