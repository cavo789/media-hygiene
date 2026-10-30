"""What `mh` says and waits for when the port of the pages is taken (0253, 0503).

A program that is not a container listening on the port (another local server) is
named with its process number (0253), Docker's own listeners excepted. A socket whose
owner has just exited (an mh page stopped a moment ago) is not a holder: Windows shows
it under PID 0 (the System Idle Process) until it is released, `ss` with no process.
`mh` waits for it, polling, a line said once; only a port still taken at the end is
refused (0503). A home page step stops the home page, then starts its own page at once
on the same port: the normal path, not a rare race.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from media_hygiene.i18n import _
from media_hygiene.services.launcher_menu import with_variable

# Docker's own programs listening for a published port (Docker Desktop on Windows, the
# engine on Linux): never "another program" holding the port of the pages (0253).
DOCKER_LISTENERS: Final = (
    "com.docker.backend",
    "com.docker.proxy",
    "wslrelay",
    "vpnkit",
    "docker-proxy",
    "rootlesskit",
    "dockerd",
)
# How long a port being released is waited for, and how often it is checked (0503).
# Estimated from the maintainer's report (freed "a few seconds later"); measured by the
# `port` step of tests/measure/mh-measure.ps1. A constant, not a setting (few settings).
PORT_RELEASE_SECONDS: Final = 10
PORT_POLL_MILLISECONDS: Final = 500


@dataclass(frozen=True, slots=True)
class PortGuard:
    """The lines of the port check, `${port}` in place, and Docker's names."""

    busy: str  # another program; holds `${name}` and `${process}`
    releasing: str  # a socket being released: waited for
    released: str  # still not released at the end of the wait: refused
    listeners: tuple[str, ...] = DOCKER_LISTENERS
    wait: int = PORT_RELEASE_SECONDS
    poll: int = PORT_POLL_MILLISECONDS


def port_guard() -> PortGuard:
    """Translate the lines of the port check, the shell variables in place.

    Returns:
        The lines, `${port}`, `${name}` and `${process}` in place.
    """
    busy = _(
        "The port {port} of the mh pages is used by another program, {name} "
        "(process {process}): close it, then type the command again; or "
        "choose another port, [review] port in config.toml, then mh update."
    )
    releasing = _(
        "The port {port} of the mh pages is still being released (an mh page "
        "has just stopped): waiting a few seconds..."
    )
    released = _(
        "The port {port} of the mh pages is not released yet by Windows: wait a "
        "few seconds, then type the command again; or choose another port, "
        "[review] port in config.toml, then mh update."
    )
    return PortGuard(
        busy=with_variable(busy, "{port}", "${port}")
        .replace("{name}", "${name}")
        .replace("{process}", "${process}"),
        releasing=with_variable(releasing, "{port}", "${port}"),
        released=with_variable(released, "{port}", "${port}"),
    )
