"""When a run started, read from its identifier."""

from __future__ import annotations

from datetime import datetime
from typing import Final

_RUN_STAMP: Final = "%Y%m%d-%H%M%S"
_STAMP_LENGTH: Final = len("20260925-183015")


def run_started(run_id: str) -> datetime:
    """When a run started, from its identifier (local time, as it was named).

    Args:
        run_id: E.g. `20260925-183015` or `20260925-183015-2`.

    Returns:
        An aware moment.
    """
    naive = datetime.strptime(run_id[:_STAMP_LENGTH], _RUN_STAMP)  # noqa: DTZ007
    return naive.astimezone()
