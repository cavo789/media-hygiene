"""More pages the home server serves itself: `step_watch.SERVED_HERE` lists them."""

from __future__ import annotations

from types import MappingProxyType
from typing import Final

QUARANTINE_PAGE: Final = "/quarantine/"  # `services/pages_here` (0591, 0594)
IMPORT_PAGE: Final = "/import/"  # `services/pages_here` (0590)
INTRUDERS_PAGE: Final = "/review/intruders/"  # `services/review_kinds` (0594)
SERVED_MORE: Final[MappingProxyType[tuple[str, ...], str]] = MappingProxyType(
    {
        ("undo", "--pick"): QUARANTINE_PAGE,
        ("import", "--pick"): IMPORT_PAGE,
        ("review", "--intruders"): INTRUDERS_PAGE,
    }
)
