"""The damaged files' page (0783), served by the home server under `/repair/`."""

from __future__ import annotations

from typing import Final

from media_hygiene.review.repair_app import RESTORE_PATH
from media_hygiene.search.undo_api import UNDO_PATH
from media_hygiene.services.pick_page_serving import pick_page

PAGE_TEMPLATE: Final = "repair.html.j2"


def repair_page() -> bytes:
    """Render the page; its paths relative to it.

    Returns:
        The page, in the language in use.
    """
    return pick_page(
        PAGE_TEMPLATE, {"restore_path": RESTORE_PATH, "undo_path": UNDO_PATH}
    )
