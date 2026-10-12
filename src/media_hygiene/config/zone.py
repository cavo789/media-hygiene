"""The user's time zone, which a Docker container does not know by itself.

Docker Desktop runs containers in UTC. `[general] timezone` (or the usual `-e TZ=…`)
names the user's zone; it is installed as the process zone, so every local time of the
run (folder names, run identifiers, the terminal) follows it.
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta
from typing import Final
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from media_hygiene.i18n import _

_TZ_VARIABLE: Final = "TZ"


def check_timezone(name: str) -> str:
    """Accept an IANA zone name such as `Europe/Brussels`, or nothing.

    Args:
        name: The configured name.

    Returns:
        The name, unchanged.

    Raises:
        ValueError: No zone has this name.
    """
    if not name:
        return name
    try:
        ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        message = _(
            "unknown time zone '{name}', expected a name like 'Europe/Brussels'"
        ).format(name=name)
        raise ValueError(message) from exc
    return name


def apply_timezone(name: str) -> None:
    """Make the configured zone the local time of this process.

    Args:
        name: An IANA zone name; empty keeps the container's zone (`-e TZ=…` or UTC).
    """
    if not name:
        return
    os.environ[_TZ_VARIABLE] = name
    time.tzset()


def timezone_unknown() -> bool:
    """Tell whether nothing named the user's zone and local time is plain UTC.

    Returns:
        True in a container started without `TZ` nor `[general] timezone`.
    """
    offset = datetime.now().astimezone().utcoffset()
    return not os.environ.get(_TZ_VARIABLE) and offset == timedelta(0)
