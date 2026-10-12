"""The browser side: serve the review and search pages, run `browser.py`."""

from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from tests.support.docker import docker
from tests.support.docs.container import DUMB, Command
from tests.support.docs.terminal import tidy

if TYPE_CHECKING:
    from tests.support.docs.container import Demo

PLAYWRIGHT: Final = "1.57.0"
# Microsoft's image ships the browsers, not the Python package: a layer adds it, once.
_BROWSER_BASE: Final = f"mcr.microsoft.com/playwright/python:v{PLAYWRIGHT}-jammy"
_DOCKERFILE: Final = (
    f"FROM {_BROWSER_BASE}\nRUN pip install --no-cache-dir playwright=={PLAYWRIGHT}\n"
)
BROWSER_IMAGE: Final = f"media-hygiene-docs-browser:{PLAYWRIGHT}"
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


def build_browser() -> None:
    """Build the browser image (instant after the first time: Docker caches it)."""
    command = ["docker", "build", "--quiet", "--tag", BROWSER_IMAGE, "-"]
    # Fixed, trusted arguments; the Dockerfile comes on the standard input.
    subprocess.run(  # noqa: S603
        command, input=_DOCKERFILE, text=True, check=True, capture_output=True
    )


def start_review(demo: Demo, args: tuple[str, ...] = ("review",)) -> str:
    """Start a page served on port 8088 in its own container, and wait until it listens.

    Args:
        demo: The demo library to serve.
        args: The command: `("review",)`, `("review", "--near")`, `("search",)`.

    Returns:
        The container's name: a browser joins its network to reach 127.0.0.1:8088.

    Raises:
        RuntimeError: The page never became ready.
    """
    name = "-".join((demo.prefix, *(arg.lstrip("-") for arg in args)))
    docker("rm", "--force", name)
    command = Command(args)
    docker("run", "--detach", "--name", name, "-t", *DUMB, *demo.mounts(command),
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
    name = f"{demo.prefix}-browser"
    docker("rm", "--force", name)
    install = (
        "pip install --quiet --disable-pip-version-check --root-user-action=ignore"
    )
    script = f"{install} playwright=={PLAYWRIGHT} && python /tmp/browser.py "
    script += shlex.join(job.args)
    # --init and --ipc=host: what Playwright advises for Chromium in Docker.
    docker("create", "--name", name, "--network", job.network, "--init",
           "--ipc", "host", "-v", f"{demo.volume('reports')}:/reports:ro",
           BROWSER_IMAGE, "sh", "-c", script)  # fmt: skip
    for source in (_SCRIPT, _SERVED, *sorted(_SCRIPT.parent.glob("*.js"))):
        docker("cp", str(source), f"{name}:/tmp/{source.name}")
    docker("cp", str(shots), f"{name}:/shots")
    docker("start", name)
    code = docker("wait", name).stdout.strip()
    if code != "0":
        log = docker("logs", name)
        docker("rm", name)
        return f"{log.stdout}{log.stderr}" or f"exit code {code}"
    docker("cp", f"{name}:/shots/.", str(shots))
    docker("rm", name)
    return ""
