"""What `clean` says of the copies it replaces by hard links (a pair keeping both)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _, ngettext
from media_hygiene.plan.pair_links import linked_count, linked_size

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.plan.models import CleanPlan


def tell_links(output: Output, plan: CleanPlan) -> None:
    """Say plainly what a hard link is, before any copy becomes one (0213).

    Args:
        output: Where to say it.
        plan: What would be cleaned.
    """
    if not linked_count(plan):
        return
    output.info(
        _(
            "🔗 A link is one photo under two names: an edit saved in place shows "
            "under both names, deleting one name frees nothing while the other "
            "remains, and a backup tool may count it twice. 'undo' makes each name "
            "an independent file again."
        )
    )


def link_phrases(plan: CleanPlan) -> list[str]:
    """The phrase of the copies made links in the question of `clean`, if any.

    Args:
        plan: What would be cleaned.

    Returns:
        One phrase, lower case, or none.
    """
    count = linked_count(plan)
    if not count:
        return []
    phrase = ngettext(
        "replace {count} duplicate copy by a link to its kept file ({size} freed, "
        "both names stay)",
        "replace {count} duplicate copies by links to their kept files ({size} "
        "freed, both names stay)",
        count,
    )
    size = human_size(linked_size(plan))
    return [phrase.format(count=human_number(count), size=size)]
