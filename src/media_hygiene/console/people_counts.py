"""What the console says of the photos a `people` run analyses (0803).

The photos never analysed and those analysed before whose turn only is still to guess
(a run after the version that guesses turns) are counted apart: the second are no new
photos, and go faster.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import ngettext

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.services.people import PeopleWork


def show_missing(output: Output, work: PeopleWork) -> None:
    """Say how many photos are still to analyse, and whose turn is still to guess.

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
                "{count} photo of {total} whose turn is still to guess (analysed "
                "before, not new).",
                "{count} photos of {total} whose turn is still to guess (analysed "
                "before, not new).",
                work.turn_only,
            ).format(count=human_number(work.turn_only), total=total)
        )
