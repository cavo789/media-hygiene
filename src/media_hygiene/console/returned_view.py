"""What `clean` says of the files set aside before that came back (0216)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import ngettext
from media_hygiene.plan.returned import returned_moves, returned_size

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.plan.models import CleanPlan


def tell_returned(output: Output, plan: CleanPlan) -> None:
    """Say, on a line of its own, that files set aside before go back (`clean`).

    And how many files deleted in the Explorer are remembered (0224).

    Args:
        output: Where to say it.
        plan: What would be cleaned.
    """
    marked = sum(answer.deleted for answer in plan.gone)
    if marked:
        remembered = ngettext(
            "🗑️ {count} file you deleted in the Explorer will be remembered: if it "
            "comes back, it is set aside.",
            "🗑️ {count} files you deleted in the Explorer will be remembered: if they "
            "come back, they are set aside.",
            marked,
        )
        output.info(remembered.format(count=human_number(marked)))
    count = len(returned_moves(plan))
    if not count:
        return
    line = ngettext(
        "↩️ {count} photo or video you had already set aside is back ({size}): "
        "back to the quarantine.",
        "↩️ {count} photos and videos you had already set aside are back ({size}): "
        "back to the quarantine.",
        count,
    )
    size = human_size(returned_size(plan))
    output.info(line.format(count=human_number(count), size=size))


def returned_phrases(plan: CleanPlan) -> list[str]:
    """The phrase of the files back in the question of `clean`, if any.

    Args:
        plan: What would be cleaned.

    Returns:
        One phrase, lower case, or none.
    """
    count = len(returned_moves(plan))
    if not count:
        return []
    phrase = ngettext(
        "move {count} file you had set aside, back since, to the quarantine again",
        "move {count} files you had set aside, back since, to the quarantine again",
        count,
    )
    return [phrase.format(count=human_number(count))]
