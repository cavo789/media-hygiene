"""More pages the home server serves itself: `step_watch.SERVED_HERE` lists them."""

from __future__ import annotations

from types import MappingProxyType
from typing import Final
from urllib.parse import quote

from media_hygiene.search.app import SEARCH_PAGE_PATH

QUARANTINE_PAGE: Final = "/quarantine/"  # `services/pages_here` (0591, 0594)
IMPORT_PAGE: Final = "/import/"  # `services/pages_here` (0590)
INTRUDERS_PAGE: Final = "/review/intruders/"  # `services/review_kinds` (0594)
SHRINK_PAGE: Final = "/shrink/"  # `services/shrink_here` (0599)
REPAIR_PAGE: Final = "/repair/"  # `services/pages_here` (0783)
DISK_PURGE_PATH: Final = "/disk-space/api/purge"  # `services/disk_here` (0616)
SERVED_MORE: Final[MappingProxyType[tuple[str, ...], str]] = MappingProxyType(
    {
        ("search",): SEARCH_PAGE_PATH,  # the former name of `library` (0486)
        ("undo", "--pick"): QUARANTINE_PAGE,
        ("import", "--pick"): IMPORT_PAGE,
        ("review", "--intruders"): INTRUDERS_PAGE,
        ("shrink", "--try"): SHRINK_PAGE,
        ("clean", "--repair"): REPAIR_PAGE,
    }
)


BACK_TO_HISTORY: Final = "history"  # `?back=`: the purge lands back on History (0631)


def purge_page(run_id: str, back: str = "") -> str:
    """Where a run's *Purge* starts: its files, then the button (0616, 0631).

    Args:
        run_id: The run.
        back: The page the purge lands back on (`BACK_TO_HISTORY`); empty: Disk space.

    Returns:
        The quarantine's page on that run.
    """
    page = f"{QUARANTINE_PAGE}?run={quote(run_id, safe='')}&purge=1"
    return f"{page}&back={back}" if back else page


def purge_step_page(words: tuple[str, ...]) -> str | None:
    """The page of a `purge <run>` chosen on a page: never a question in the window.

    Args:
        words: The command's words, without `mh`.

    Returns:
        Its page; None for any other step, `--yes` (the page has asked) and `--to` too.
    """
    match words:
        case ("purge", run_id) if not run_id.startswith("-"):
            return purge_page(run_id)
    return None
