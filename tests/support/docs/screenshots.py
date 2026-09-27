"""The browser side: serve the burst review, run `browser.py` in Playwright's image."""

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
BROWSER_IMAGE: Final = f"media-dedup-docs-browser:{PLAYWRIGHT}"
_SCRIPT: Final = Path(__file__).with_name("browser.py")
_READY: Final = "8080"  # the review says it listens on port 8080
_WAIT_SECONDS: Final = 300


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


def start_review(demo: Demo) -> str:
    """Start the burst review in its own container, and wait until it listens.

    Args:
        demo: The demo library to review.

    Returns:
        The container's name: a browser joins its network to reach 127.0.0.1:8080.

    Raises:
        RuntimeError: The review never became ready.
    """
    name = f"{demo.prefix}-review"
    docker("rm", "--force", name)
    command = Command(("review",))
    docker("run", "--detach", "--name", name, "-t", *DUMB, *demo.mounts(command),
           *demo.tool(command))  # fmt: skip
    for _ in range(_WAIT_SECONDS):
        if _READY in docker("logs", name).stdout:
            return name
        time.sleep(1)
    message = f"the review did not start: {docker('logs', name).stdout}"
    raise RuntimeError(message)


def stop_review(name: str) -> str:
    """Stop the review (Ctrl+C would), and return what its terminal showed.

    Args:
        name: The container of the review.

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
    name = f"{demo.prefix}-browser"
    docker("rm", "--force", name)
    install = (
        "pip install --quiet --disable-pip-version-check --root-user-action=ignore"
    )
    script = f"{install} playwright=={PLAYWRIGHT} && python /tmp/browser.py "
    script += shlex.join(job.args)
    docker("create", "--name", name, "--network", job.network,
           "-v", f"{demo.volume('reports')}:/reports:ro", BROWSER_IMAGE,
           "sh", "-c", script)  # fmt: skip
    for source in (_SCRIPT, *sorted(_SCRIPT.parent.glob("*.js"))):
        docker("cp", str(source), f"{name}:/tmp/{source.name}")
    docker("cp", str(shots), f"{name}:/shots")
    docker("start", name)
    code = docker("wait", name).stdout.strip()
    if code != "0":
        log = docker("logs", name)
        docker("rm", name)
        message = f"browser {job.args}: {log.stdout}{log.stderr}"
        raise RuntimeError(message)
    docker("cp", f"{name}:/shots/.", str(shots))
    docker("rm", name)
