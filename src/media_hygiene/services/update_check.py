"""Is a newer version published? Docker Hub asked at most once a day (0267).

What leaves the machine: one request to hub.docker.com, the tags of the published
image; no data about the photos. Docker Hub sees the address and the repository
name, as with a `docker pull`. A local build never asks, `[general] check_updates =
false` turns it off. The answer and its time are kept in `/cache`, read again before
asking; any failure (offline, a timeout, a 429, an answer it cannot read) is silent
and kept too: the next try comes the next day.
"""

from __future__ import annotations

import json
import re
import urllib.request
from datetime import UTC, datetime, timedelta
from importlib.metadata import version
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.constants import APP_NAME, HOME_PAGE
from media_hygiene.paths.docker_run import PUBLISHED_IMAGE, running_image

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

type Fetch = Callable[[str], bytes]

_NAMESPACE, _REPOSITORY = PUBLISHED_IMAGE.split("/")
TAGS_URL: Final = (
    f"https://hub.docker.com/v2/namespaces/{_NAMESPACE}/repositories/{_REPOSITORY}"
    "/tags?page_size=25&ordering=last_updated"
)
RELEASES_URL: Final = f"{HOME_PAGE}/releases"
CHECK_FILE_NAME: Final = "update-check.json"
TIMEOUT_S: Final = 3.0
MAX_BYTES: Final = 1024 * 1024
_EVERY: Final = timedelta(days=1)
_VERSION: Final = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


class _Frozen(BaseModel):
    """Frozen, no field left unknown."""

    model_config = ConfigDict(frozen=True, extra="forbid")


class UpdateNotice(_Frozen):
    """A newer version: its number and where to read what changes."""

    version: str  # e.g. "0.5.0"
    notes: str = RELEASES_URL


class _Checked(_Frozen):
    """The last time Docker Hub was asked, and the newest version it gave."""

    checked_at: datetime
    latest: str | None = None


def fetch_tags(url: str) -> bytes:
    """Ask Docker Hub, three seconds at most.

    Args:
        url: The address of the tags.

    Returns:
        The body of the answer, at most `MAX_BYTES`.
    """
    agent = f"{APP_NAME}/{version(APP_NAME)} (+{HOME_PAGE})"
    request = urllib.request.Request(url, headers={"User-Agent": agent})  # noqa: S310 - https
    with urllib.request.urlopen(request, timeout=TIMEOUT_S) as answer:  # noqa: S310
        return bytes(answer.read(MAX_BYTES))


def newer_version(runtime: Runtime, fetch: Fetch | None = None) -> UpdateNotice | None:
    """Tell whether a newer version than this one is published.

    Args:
        runtime: Settings and mount points: `/cache` keeps the answer.
        fetch: What asks Docker Hub; None: `fetch_tags`, read when called.

    Returns:
        The newer version; None when there is none, or when nothing could tell.
    """
    if not runtime.settings.general.check_updates or running_image() != PUBLISHED_IMAGE:
        return None
    running = _parsed(version(APP_NAME))
    latest = _latest(runtime.locations.cache_dir / CHECK_FILE_NAME, fetch or fetch_tags)
    newest = _parsed(latest) if latest else None
    if running is None or newest is None or latest is None or newest <= running:
        return None
    return UpdateNotice(version=latest)


def _latest(path: Path, fetch: Fetch) -> str | None:
    """The newest version, from the answer of the day, or asked again.

    Args:
        path: The file keeping the last answer.
        fetch: What asks Docker Hub.

    Returns:
        The newest version published; None when it is not known.
    """
    now = datetime.now(UTC)
    known = _read(path)
    if known is not None and timedelta(0) <= now - known.checked_at < _EVERY:
        return known.latest
    latest = _ask(fetch)
    try:
        checked = _Checked(checked_at=now, latest=latest)
        path.write_text(checked.model_dump_json(), "utf-8")
    except OSError:
        pass  # a read-only or missing cache: asked again next time, still silent
    return latest


def _read(path: Path) -> _Checked | None:
    """The last answer kept, when it can be read.

    Args:
        path: The file.

    Returns:
        It; None when missing or unreadable.
    """
    try:
        return _Checked.model_validate_json(path.read_bytes())
    except OSError, ValidationError:
        return None


def _ask(fetch: Fetch) -> str | None:
    """Ask Docker Hub for the tags, and keep the highest `X.Y.Z` one.

    Args:
        fetch: What asks Docker Hub.

    Returns:
        The highest version; None on any failure or without one.
    """
    try:
        answer = json.loads(fetch(TAGS_URL))
    except OSError, ValueError:  # offline, a timeout, a 429, not JSON
        return None
    results = answer.get("results") if isinstance(answer, dict) else None
    listed = results if isinstance(results, list) else []
    names = [result.get("name") for result in listed if isinstance(result, dict)]
    versions = [name for name in names if isinstance(name, str) and _parsed(name)]
    return max(versions, key=lambda name: _parsed(name) or (), default=None)


def _parsed(name: str) -> tuple[int, ...] | None:
    """The numbers of a version written `X.Y.Z`.

    Args:
        name: A tag or a version, e.g. `0.5.0`, `latest`, `0.5`.

    Returns:
        Its three numbers; None for anything else.
    """
    match = _VERSION.match(name)
    return tuple(int(part) for part in match.groups()) if match else None
