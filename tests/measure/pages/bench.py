"""Time each read route the pages call, on a synthetic library (0678).

`python -m tests.measure.pages.bench <files> <folder> [--profile <route>]` builds the
index once into `<folder>/<files>/pristine.sqlite` (reused while it is there; copied
into the cache at each run: the people page writes its face groups), starts `home` in
this process against it, as `mh` does (the server's router, its pool, its runtime), and
sends each route through the router: no socket, so the figures are the server's work,
not the browser's nor the network's. The warm-up of the first clicks (0677) is not
started (the server's `ready` callback is never called): *cold* is the first request
of each route in a fresh process, the routes in the order below (a route opening the
index pays for the ones after it); *warm* is the median of the next runs. Prints
(and writes to `--out`) one JSON document: the figures per route, the peak memory,
the build time.
"""

from __future__ import annotations

import argparse
import contextlib
import cProfile
import json
import os
import pstats
import resource
import shutil
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.app import build_app
from media_hygiene.constants import Locale
from media_hygiene.i18n import install
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.http import Request
from media_hygiene.services import home
from tests.measure.pages.library import Library, build

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.ending import EndingDoor

WARM_RUNS: Final = 5
_LOCAL: Final = {"host": "127.0.0.1"}
_JSON: Final = {**_LOCAL, "content-type": "application/json"}


@dataclass(frozen=True, slots=True)
class Route:
    """One request a page sends."""

    name: str
    method: str
    path: str
    body: dict[str, object] | None = None


ROUTES: Final = (
    Route("home state", "GET", "/api/state"),
    Route("search: words", "POST", "/api/search", {"text": "plage"}),
    Route(
        "search: a period", "POST", "/api/search", {"year_from": 2015, "year_to": 2015}
    ),
    Route("search: a place", "POST", "/api/search", {"text": "durbuy"}),
    Route("search: nothing typed", "POST", "/api/search", {"text": ""}),
    Route("folders", "GET", "/api/folders"),
    Route("events: a year", "GET", "/api/events/span/2015-01-01..2015-12-31"),
    Route("events: found in folders", "GET", "/api/found-events"),
    Route("people page", "GET", "/people/"),
    Route("people groups", "GET", "/people/api/groups"),
    Route("places page (clusters built)", "GET", "/places/"),
    Route("places clusters", "GET", "/places/api/state"),
    Route("albums", "GET", "/api/album-list"),
)


def _point_mounts(base: Path) -> None:
    """Point every mount point of the tool below `base`.

    Args:
        base: The folder of this size.
    """
    for kind in MountKind:
        folder = base / kind.value
        folder.mkdir(parents=True, exist_ok=True)
        os.environ[f"MEDIA_HYGIENE_{kind.value.upper()}_DIR"] = str(folder)
    (base / MountKind.DATA.value / "c").mkdir(exist_ok=True)


async def _one(door: EndingDoor, route: Route) -> tuple[float, int, int]:
    """Send a route once.

    Args:
        door: The server's door.
        route: The route.

    Returns:
        Milliseconds, the status, the body's bytes.
    """
    body = json.dumps(route.body).encode() if route.body is not None else b""
    request = Request(route.method, route.path, _JSON if route.body else _LOCAL, body)
    start = time.perf_counter()
    response = await door.handle(request)
    return (
        (time.perf_counter() - start) * 1000,
        int(response.status),
        len(response.body),
    )


def _serving(
    figures: dict[str, object], profiled: str | None, skipped: frozenset[str]
) -> Callable[..., object]:
    """The replacement of `serve_until_ended`: time the routes, then Ctrl+C.

    Args:
        figures: Filled with one entry per route.
        profiled: A route's name to profile (its warm runs), or None.
        skipped: The routes' names left out (too slow at this size).

    Returns:
        The coroutine function.
    """

    async def serve(door: EndingDoor, _port: int, _ready: Callable[[int], None]) -> int:
        for route in (each for each in ROUTES if each.name not in skipped):
            cold, status, size = await _one(door, route)
            profile = cProfile.Profile() if route.name == profiled else None
            if profile is not None:
                profile.enable()
            warm = [(await _one(door, route))[0] for _ in range(WARM_RUNS)]
            if profile is not None:
                profile.disable()
                pstats.Stats(profile, stream=sys.stderr).sort_stats(
                    "tottime"
                ).print_stats(25)
            figures[route.name] = {
                "status": status,
                "bytes": size,
                "cold_ms": round(cold, 1),
                "warm_ms": round(statistics.median(warm), 1),
            }
        raise KeyboardInterrupt

    return serve


def _arguments() -> argparse.Namespace:
    """The command line.

    Returns:
        Its arguments.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", type=int)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--profile", default=None, help="a route's name")
    parser.add_argument(
        "--skip", action="append", default=[], help="a route's name left out"
    )
    parser.add_argument("--out", type=Path, default=None, help="the JSON file written")
    return parser.parse_args()


def _prepare(files: int, folder: Path) -> float:
    """Point the mounts, build the index if missing, copy it into the cache.

    Args:
        files: How many files.
        folder: Where every size lives.

    Returns:
        The seconds the build took; 0 when it was there.
    """
    base = folder / str(files)
    _point_mounts(base)
    index = base / MountKind.CACHE.value / "index.sqlite"
    pristine = base / "pristine.sqlite"
    built = 0.0
    if not pristine.exists():
        start = time.perf_counter()
        build(Library(pristine, base / MountKind.DATA.value / "c", files))
        built = time.perf_counter() - start
    # The pages write into the index (the face groups, 0432): each run starts afresh.
    for leftover in index.parent.glob(f"{index.name}*"):
        leftover.unlink()
    shutil.copyfile(pristine, index)
    return built


def main() -> None:
    """Build if needed, serve, time, print."""
    arguments = _arguments()
    built = _prepare(arguments.files, arguments.folder)
    install(Locale.EN)
    routes: dict[str, object] = {}
    # As `tests/support/home_serving` does: the server's loop replaced by the bench.
    vars(home)["serve_until_ended"] = _serving(
        routes, arguments.profile, frozenset(arguments.skip)
    )
    started = time.perf_counter()
    with contextlib.suppress(SystemExit):
        build_app()(
            args=["home", "--port", "8099"],
            prog_name="media-hygiene",
            standalone_mode=False,
        )
    document = json.dumps(
        {
            "files": arguments.files,
            "build_s": round(built, 1),
            "serve_s": round(time.perf_counter() - started, 1),
            "peak_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024,
            "routes": routes,
        },
        indent=1,
    )
    if arguments.out is not None:
        arguments.out.write_text(document, encoding="utf-8")
    print(document)  # noqa: T201 - the bench's output


if __name__ == "__main__":
    main()
