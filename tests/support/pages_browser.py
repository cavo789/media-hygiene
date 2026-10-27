"""Chromium in Microsoft's Playwright image: the docs' shots and the page tests.

The image is built once (Docker caches it), a script of this repository copied in
and run (`python /tmp/<script> <args>`), its folder `/shots` copied in and back.
Python 3.10 runs in that image: nothing newer in the scripts it runs.
"""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from tests.support.docker import docker

if TYPE_CHECKING:
    from pathlib import Path

PLAYWRIGHT: Final = "1.57.0"
# Microsoft's image ships the browsers, not the Python package: a layer adds it, once.
_BROWSER_BASE: Final = f"mcr.microsoft.com/playwright/python:v{PLAYWRIGHT}-jammy"
_DOCKERFILE: Final = (
    f"FROM {_BROWSER_BASE}\nRUN pip install --no-cache-dir playwright=={PLAYWRIGHT}\n"
)
BROWSER_IMAGE: Final = f"media-hygiene-docs-browser:{PLAYWRIGHT}"
_INSIDE: Final = "/tmp"  # noqa: S108  # in the browser's container
_INSTALL: Final = (
    "pip install --quiet --disable-pip-version-check --root-user-action=ignore"
)


@dataclass(frozen=True, slots=True)
class BrowserRun:
    """One run of a script in the Playwright image.

    Attributes:
        name: The container's name (removed first, and after).
        scripts: The files copied to /tmp; the first one is run.
        args: Its arguments.
        network: The network it joins (`host`: the pages `mh` publishes on 127.0.0.1).
        options: More `docker create` options (volumes).
    """

    name: str
    scripts: tuple[Path, ...]
    args: tuple[str, ...]
    network: str
    options: tuple[str, ...] = ()


def build_browser() -> None:
    """Build the browser image (instant after the first time: Docker caches it)."""
    command = ["docker", "build", "--quiet", "--tag", BROWSER_IMAGE, "-"]
    # Fixed, trusted arguments; the Dockerfile comes on the standard input.
    subprocess.run(  # noqa: S603
        command, input=_DOCKERFILE, text=True, check=True, capture_output=True
    )


def run_browser(run: BrowserRun, shots: Path) -> str:
    """Run the script once in the Playwright image.

    Args:
        run: The script, its arguments and its network.
        shots: A folder of this machine, copied in as /shots and back.

    Returns:
        Empty when it worked, its log otherwise (its /shots copied back either way).
    """
    docker("rm", "--force", run.name)
    command = shlex.join((f"{_INSIDE}/{run.scripts[0].name}", *run.args))
    script = f"{_INSTALL} playwright=={PLAYWRIGHT} && python {command}"
    # --init and --ipc=host: what Playwright advises for Chromium in Docker.
    docker("create", "--name", run.name, "--network", run.network, "--init",
           "--ipc", "host", *run.options,
           BROWSER_IMAGE, "sh", "-c", script)  # fmt: skip
    for source in run.scripts:
        docker("cp", str(source), f"{run.name}:{_INSIDE}/{source.name}")
    docker("cp", str(shots), f"{run.name}:/shots")
    docker("start", run.name)
    code = docker("wait", run.name).stdout.strip()
    docker("cp", f"{run.name}:/shots/.", str(shots))
    log = docker("logs", run.name)
    docker("rm", run.name)
    if code == "0":
        return ""
    return f"{log.stdout}{log.stderr}" or f"exit code {code}"
