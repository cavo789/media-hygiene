"""The zone of the Windows host, named by `mh.ps1`, as the IANA zone a container knows.

Windows PowerShell 5.1 gives `(Get-TimeZone).Id`, a Windows id (`Romance Standard
Time`), and .NET Framework cannot turn it into an IANA name. `mh.ps1` passes it on at
each run in `MEDIA_HYGIENE_WINDOWS_ZONE`; the CLDR table vendored in `data/` maps it.
"""

from __future__ import annotations

import os
from functools import cache
from importlib import resources
from typing import Final
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from media_hygiene.constants import ENV_PREFIX

WINDOWS_ZONE_VARIABLE: Final = f"{ENV_PREFIX}WINDOWS_ZONE"
_TABLE: Final = "windows_zones.tsv"
_SEPARATOR: Final = "\t"


@cache
def _zones() -> dict[str, str]:
    """Read the CLDR table once: Windows id → IANA zone.

    Returns:
        Every Windows zone of the table.
    """
    text = resources.files(__package__).joinpath("data", _TABLE).read_text("utf-8")
    return dict(line.split(_SEPARATOR, 1) for line in text.splitlines() if line)


def iana_zone(windows_id: str) -> str:
    """The IANA zone of a Windows zone id.

    Args:
        windows_id: E.g. `Romance Standard Time`.

    Returns:
        E.g. `Europe/Paris`; empty for an id the table or the container does not know.
    """
    zone = _zones().get(windows_id.strip(), "")
    if not zone:
        return ""
    try:
        ZoneInfo(zone)
    except ZoneInfoNotFoundError:
        return ""
    return zone


def host_zone() -> str:
    """The zone `mh.ps1` found on the Windows host, when it says one.

    Returns:
        An IANA zone, or empty.
    """
    return iana_zone(os.environ.get(WINDOWS_ZONE_VARIABLE, ""))
