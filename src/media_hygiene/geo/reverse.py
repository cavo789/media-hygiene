"""Name a position online, once the user said Yes (0474): Nominatim's reverse lookup.

The only place a position leaves the machine, and never without the user's consent
(`services.place_names` asks each time). The position sent is rounded (`DECIMALS`,
about 110 m): a cluster of photos, never one photo. One request per second at most,
an identifying User-Agent (the policy of
https://operations.osmfoundation.org/policies/nominatim/); `zoom` 18 names buildings
and monuments. The standard library's `urllib`: no new dependency.
"""

from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final
from urllib.parse import urlencode

from media_hygiene.geo.nominatim import INTERVAL_S, TIMEOUT_S, Service, fetch

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.geo.distance import Point
    from media_hygiene.geo.nominatim import Fetcher

REVERSE: Final = "/reverse"
DECIMALS: Final = 3  # about 110 m: the cluster, not the photo
ZOOM: Final = 18  # buildings and monuments


@dataclass(frozen=True, slots=True)
class Pace:
    """How requests are sent and spaced: replaced in tests, never the network there."""

    fetch: Fetcher = fetch
    clock: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep


def rounded(point: Point) -> tuple[float, float]:
    """A position as sent and cached: rounded to `DECIMALS`.

    Args:
        point: A position.

    Returns:
        Its latitude and longitude, rounded.
    """
    return round(point.latitude, DECIMALS), round(point.longitude, DECIMALS)


class ReverseLookup:
    """Names positions, one request per second at most."""

    def __init__(self, service: Service, pace: Pace | None = None) -> None:
        """Prepare the lookups.

        Args:
            service: The instance, the language, the User-Agent.
            pace: How to send and space the requests.
        """
        self._service = service
        self._pace = pace or Pace()
        self._last: float | None = None

    def name_at(self, spot: tuple[float, float]) -> str:
        """The name OpenStreetMap gives a rounded position.

        Args:
            spot: A position, rounded (`rounded`).

        Returns:
            The name of the building, monument or street there; empty when it has
            none, or when the answer is not one.

        Raises:
            OSError: The service is unreachable or refused (URLError, HTTPError and
                timeouts included).
        """
        if self._last is not None:
            wait = self._last + INTERVAL_S - self._pace.clock()
            if wait > 0:
                self._pace.sleep(wait)
        try:
            body = self._pace.fetch(self._request(spot), TIMEOUT_S)
        finally:
            self._last = self._pace.clock()
        try:
            answer = json.loads(body)
        except ValueError:
            return ""
        name = answer.get("name") if isinstance(answer, dict) else None
        return name.strip() if isinstance(name, str) else ""

    def _request(self, spot: tuple[float, float]) -> urllib.request.Request:
        """The request for one position.

        Args:
            spot: The rounded position.

        Returns:
            The request.
        """
        query = urlencode(
            {"lat": spot[0], "lon": spot[1], "format": "jsonv2", "zoom": ZOOM}
        )
        headers = {
            "User-Agent": self._service.agent,
            "Accept-Language": self._service.language,
        }
        url = f"{self._service.url.rstrip('/')}{REVERSE}?{query}"
        return urllib.request.Request(url, headers=headers)  # noqa: S310 - http(s)
