"""The choices waiting in `decisions.json`, page by page, for the home page (0522).

Intruder files and the people page's photos lie in its `chosen` key too (0587): their
`found_by` tells them from `library`'s, so each page is named with its own count.

Every review page and `library` write their choices into the one decisions file of the
reports folder, each under its own key; one `clean --decisions` (the home page's
`apply` step) applies them all in one journal run, so one `mh undo` takes them all back.
The home page shows how many wait on which page, read from disk each time: once applied,
the file is archived and the count reads 0.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.plan.near_review import NearAction
from media_hygiene.plan.review import PairAction
from media_hygiene.report.burst_decisions import BurstStatus
from media_hygiene.report.chosen_decisions import PEOPLE_FOUND_BY
from media_hygiene.report.decisions import read_decisions
from media_hygiene.review.home_parts import HomePending, PendingPage
from media_hygiene.review.place import DEFAULT_DECISIONS
from media_hygiene.review.served_more import INTRUDERS_PAGE
from media_hygiene.review.step_watch import (
    BURSTS_PAGE,
    GONE_PAGE,
    JUNK_PAGE,
    NEAR_REVIEW_PAGE,
    PAIRS_PAGE,
)
from media_hygiene.search.app import SEARCH_PAGE_PATH
from media_hygiene.services.intruder_pick import FOUND_BY as INTRUDER

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.report.decisions import DecisionsFile


def home_pending(reports: Path | None) -> HomePending | None:
    """Count the choices of each page still waiting in the decisions file.

    Args:
        reports: The reports folder; None when it is not mounted.

    Returns:
        The total and the pages that have some; None when nothing waits.
    """
    if reports is None or not (reports / DEFAULT_DECISIONS).is_file():
        return None
    try:
        file = read_decisions(reports / DEFAULT_DECISIONS)
    except DecisionsError:
        return None  # `clean` says why: the page shows no count it cannot prove
    pages = tuple(page for page in _pages(file) if page.count)
    if not pages:
        return None
    return HomePending(total=sum(page.count for page in pages), pages=pages)


def _pages(file: DecisionsFile) -> tuple[PendingPage, ...]:
    """Each page's count, in the order of the cycle.

    Args:
        file: The decisions read.

    Returns:
        Every page, its count possibly 0.
    """
    bursts = sum(
        len(burst.discarded)
        for burst in file.bursts
        if burst.status is BurstStatus.DONE
    )
    intruders = sum(item.found_by == INTRUDER for item in file.chosen)
    people = sum(item.found_by.startswith(PEOPLE_FOUND_BY) for item in file.chosen)
    return (
        PendingPage(label=_("Burst series"), count=bursts, url=BURSTS_PAGE),
        PendingPage(
            label=_("Near duplicates"),
            count=sum(group.action is not NearAction.PLANNED for group in file.near),
            url=NEAR_REVIEW_PAGE,
        ),
        PendingPage(
            label=_("Folder pairs"),
            count=sum(pair.action is not PairAction.PLANNED for pair in file.pairs),
            url=PAIRS_PAGE,
        ),
        PendingPage(
            label=_("Unwanted photos"),
            count=sum(entry.aside for entry in file.unwanted),
            url=JUNK_PAGE,
        ),
        PendingPage(
            label=_("Files gone"),
            count=sum(entry.deleted for entry in file.gone),
            url=GONE_PAGE,
        ),
        PendingPage(label=_("Intruder files"), count=intruders, url=INTRUDERS_PAGE),
        PendingPage(label=_("People"), count=people),  # its own server: no link here
        PendingPage(
            label=_("Library"),
            count=len(file.chosen) - intruders - people,
            url=SEARCH_PAGE_PATH,
        ),
    )
