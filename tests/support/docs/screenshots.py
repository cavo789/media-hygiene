"""The browser side: serve the review and search pages, run `browser.py`."""

from __future__ import annotations

import shlex
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from tests.support.docker import docker
from tests.support.docs.container import DUMB, Command
from tests.support.docs.terminal import tidy
from tests.support.pages_browser import BrowserRun, run_browser

if TYPE_CHECKING:
    from tests.support.docs.container import Demo

_SCRIPT: Final = Path(__file__).with_name("browser.py")
_SERVED: Final = _SCRIPT.with_name("served.py")  # imported by browser.py
_READY: Final = "127.0.0.1:8088"  # the review and the search print their address
_WAIT_SECONDS: Final = 300
# Chromium sometimes dies while starting, before any page: nothing done yet, retry.
_LAUNCH_FAILED: Final = "BrowserType.launch"
_ATTEMPTS: Final = 2


@dataclass(frozen=True, slots=True)
class Job:
    """What the browser does, and which network it sees."""

    network: str
    args: tuple[str, ...]


def start_review(
    demo: Demo, args: tuple[str, ...] = ("review",), variables: tuple[str, ...] = ()
) -> str:
    """Start a page served on port 8088 in its own container, and wait until it listens.

    Args:
        demo: The demo library to serve.
        args: The command: `("review",)`, `("review", "--near")`, `("search",)`.
        variables: Environment variables (`NAME=value`) given to the container.

    Returns:
        The container's name: a browser joins its network to reach 127.0.0.1:8088.

    Raises:
        RuntimeError: The page never became ready.
    """
    name = "-".join((demo.prefix, *(arg.lstrip("-") for arg in args)))
    docker("rm", "--force", name)
    command = Command(args)
    environment = [item for variable in variables for item in ("-e", variable)]
    docker("run", "--detach", "--name", name, "-t", *DUMB, *environment,
           *demo.mounts(command),
           *demo.tool(command))  # fmt: skip
    for _ in range(_WAIT_SECONDS):
        if _READY in docker("logs", name).stdout:
            return name
        time.sleep(1)
    message = f"{shlex.join(args)} did not start: {docker('logs', name).stdout}"
    raise RuntimeError(message)


def stop_review(name: str) -> str:
    """Stop a served page (Ctrl+C would), and return what its terminal showed.

    Args:
        name: The container of the page.

    Returns:
        The screen, tidied.
    """
    docker("stop", name)
    screen = docker("logs", name).stdout
    docker("rm", name)
    return tidy(screen)


def shoot(demo: Demo, job: Job, shots: Path) -> None:
    """Run `browser.py` in the Playwright image; its inputs and outputs live in `shots`.

    Args:
        demo: The demo whose reports volume the browser reads.
        job: The mode, its arguments, and the network to join.
        shots: A folder of this machine, copied in as /shots and back.

    Raises:
        RuntimeError: The browser failed; its log says why.
    """
    for attempt in range(1, _ATTEMPTS + 1):
        log = _browse(demo, job, shots)
        if not log:
            return
        if _LAUNCH_FAILED not in log or attempt == _ATTEMPTS:
            message = f"browser {job.args}: {log}"
            raise RuntimeError(message)


def _browse(demo: Demo, job: Job, shots: Path) -> str:
    """Run the browser once.

    Args:
        demo: The demo whose reports volume the browser reads.
        job: The mode, its arguments, and the network to join.
        shots: A folder of this machine, copied in as /shots and back.

    Returns:
        Empty when it worked, its log otherwise.
    """
    run = BrowserRun(
        name=f"{demo.prefix}-browser",
        scripts=(_SCRIPT, _SERVED, *sorted(_SCRIPT.parent.glob("*.js"))),
        args=job.args,
        network=job.network,
        options=("-v", f"{demo.volume('reports')}:/reports:ro"),
    )
    return run_browser(run, shots)
