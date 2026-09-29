"""The inventory of an audit, in the console: dates, places, formats, video length."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.table import Table

from media_hygiene.console.formatting import human_duration, human_number, human_share
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.scan.inventory import Inventory


def inventory_table(inventory: Inventory) -> Table | None:
    """What the photos and videos say about when and where they were taken.

    Args:
        inventory: The counts of the audit.

    Returns:
        A two-column table, or None when the audit found no photo nor video.
    """
    media = inventory.images + inventory.videos
    if not media:
        return None
    table = Table(title=_("Inventory"), show_header=False, title_justify="left")
    table.add_column(style="bold")
    table.add_column(justify="right")
    if inventory.images:
        table.add_row(
            _("Photos with a shooting date"),
            human_share(inventory.dated_images, inventory.images),
        )
    if inventory.videos:
        table.add_row(
            _("Videos with a date in their tags"),
            human_share(inventory.dated_videos, inventory.videos),
        )
    table.add_row(
        _("Photos and videos with a GPS position"),
        human_share(inventory.located, media),
    )
    if inventory.formats:
        formats = " · ".join(
            f"{name} {human_number(count)}" for name, count in inventory.formats.items()
        )
        table.add_row(_("Photo formats"), formats)
    if inventory.video_seconds:
        table.add_row(
            _("Total length of the videos"), human_duration(inventory.video_seconds)
        )
    return table
