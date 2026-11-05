"""The tiles leading to a page: disk space (0539), the tidying session (0528)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.menu_entry import Space
from media_hygiene.console.formatting import human_size
from media_hygiene.i18n import _
from media_hygiene.review.home_parts import HomeTile
from media_hygiene.review.step_watch import BURSTS_PAGE, DISK_PAGE

if TYPE_CHECKING:
    from media_hygiene.services.status import Status


def page_tiles(status: Status) -> tuple[HomeTile, ...]:
    """The tiles leading to a page.

    Args:
        status: What the tool folders say.

    Returns:
        The disk space; the session too once an audit exists.
    """
    disk = HomeTile(
        id="disk",
        label=_("Disk space"),
        value=human_size(status.quarantine.size),
        sub=_("Quarantine and previews, their limits"),
        space=Space.HISTORY.value,
        url=DISK_PAGE,
    )
    if status.analysis.summary is None:
        return (disk,)
    tidy = HomeTile(
        id="tidy",
        label=_("10 minutes of tidying"),
        value=_("Start"),
        sub=_("Bursts then near duplicates, biggest gain first"),
        space=Space.CLEAN.value,
        url=BURSTS_PAGE,
        tidy=True,
    )
    return disk, tidy
