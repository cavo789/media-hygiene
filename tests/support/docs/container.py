"""Run the real image against the demo library, held in Docker volumes of its own."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from tests.support.docker import IMAGE, docker, run_image
from tests.support.docs.names import Locale
from tests.support.docs.terminal import answer_prompt, tidy

if TYPE_CHECKING:
    from tests.support.docs.names import Library

# c and d hold C:\Photos and D:\Old disk; the others are the tool's mount points.
VOLUMES: Final = ("c", "d", "journal", "quarantine", "reports", "cache", "config")
_TOOL_MOUNTS: Final = VOLUMES[2:]
DUMB: Final = (
    "-e",
    "TERM=dumb",
)  # no progress animation: the screen reads top to bottom
_IMAGE_COLUMNS: Final = ("-e", "COLUMNS=100")
_YES: Final = {Locale.EN: "y", Locale.FR: "o"}


@dataclass(frozen=True, slots=True)
class Command:
    """One media-dedup command line, and what it may see."""

    args: tuple[str, ...]
    read_only: bool = True
    photos_only: bool = False


@dataclass(frozen=True, slots=True)
class Demo:
    """The demo library of one language, and the volumes the image sees it through."""

    library: Library
    locale: Locale

    @property
    def prefix(self) -> str:
        """The name shared by the volumes and containers of this language."""
        return f"media-dedup-docs-{self.locale}"

    def volume(self, kind: str) -> str:
        """Name a volume of this demo.

        Args:
            kind: `c`, `d`, or a mount point of the tool (`journal`, …).

        Returns:
            The Docker volume name.
        """
        return f"{self.prefix}-{kind}"

    def mounts(self, command: Command) -> list[str]:
        """The `-v` options of a command.

        Args:
            command: What the command may see.

        Returns:
            The options, data folders first.
        """
        suffix = ":ro" if command.read_only else ""
        disk = self.library.names.old_disk
        options = ["-v", f"{self.volume('c')}:/data/c/Photos{suffix}"]
        if command.photos_only:
            return options
        options += ["-v", f"{self.volume('d')}:/data/d/{disk}{suffix}"]
        for kind in _TOOL_MOUNTS:
            options += ["-v", f"{self.volume(kind)}:/{kind}"]
        return options

    def tool(self, command: Command) -> list[str]:
        """The image and its arguments, in the language of this demo.

        Args:
            command: The command line.

        Returns:
            What follows the `docker run` options.
        """
        return [IMAGE, "--color", "never", "--locale", self.locale, *command.args]


def seed(demo: Demo) -> None:
    """Create fresh volumes and copy the demo library in, owned by the tool's user.

    Args:
        demo: The demo to seed.
    """
    for kind in VOLUMES:
        docker("volume", "rm", "--force", demo.volume(kind))
        docker("volume", "create", demo.volume(kind))
    holder = f"{demo.prefix}-seed"
    docker("create", "--name", holder, "-v", f"{demo.volume('c')}:/c",
           "-v", f"{demo.volume('d')}:/d", IMAGE)  # fmt: skip
    docker("cp", f"{demo.library.photos}/.", f"{holder}:/c/")
    docker("cp", f"{demo.library.disk}/.", f"{holder}:/d/")
    docker("rm", holder)
    mounts = [f"-v{demo.volume(kind)}:/{kind}" for kind in VOLUMES]
    targets = [f"/{kind}" for kind in VOLUMES]
    docker("run", "--rm", "--user", "0", "--entrypoint", "chown", *mounts, IMAGE,
           "-R", "1000:1000", *targets)  # fmt: skip


def run(demo: Demo, command: Command) -> str:
    """Run a command to completion and return what its terminal showed.

    Args:
        demo: The demo library to run against.
        command: The command line.

    Returns:
        The screen, tidied.
    """
    result = run_image("-t", *DUMB, *demo.mounts(command), *demo.tool(command))
    return tidy(result.stdout + result.stderr)


def run_confirmed(demo: Demo, command: Command) -> str:
    """Run a command that asks before acting, and answer yes in its language.

    Args:
        demo: The demo library to run against.
        command: The command line.

    Returns:
        The screen, question and answer included, tidied.
    """
    line = ["docker", "run", "--rm", "-it", *DUMB, *demo.mounts(command)]
    return tidy(answer_prompt([*line, *demo.tool(command)], _YES[demo.locale]))


def run_in_colour(demo: Demo, command: Command) -> str:
    """Run a command with ANSI colours, as a terminal would show it.

    Args:
        demo: The demo library to run against.
        command: The command line.

    Returns:
        The output, escape codes included.
    """
    colour = [IMAGE, "--color", "always", "--locale", demo.locale, *command.args]
    return run_image(*_IMAGE_COLUMNS, *demo.mounts(command), *colour).stdout


def read_file(demo: Demo, kind: str, path: str) -> str:
    """Read a file from one of the demo's volumes.

    Args:
        demo: The demo.
        kind: The volume (`reports`, `config`, …).
        path: The file, relative to the volume.

    Returns:
        Its content.
    """
    mount = f"{demo.volume(kind)}:/volume:ro"
    return docker("run", "--rm", "--entrypoint", "cat", "-v", mount, IMAGE,
                  f"/volume/{path}").stdout  # fmt: skip


def list_files(demo: Demo, kind: str) -> list[str]:
    """List the files of one of the demo's volumes.

    Args:
        demo: The demo.
        kind: The volume (`reports`, `quarantine`, …).

    Returns:
        Their paths relative to the volume, sorted.
    """
    mount = f"{demo.volume(kind)}:/volume:ro"
    found = docker("run", "--rm", "--entrypoint", "find", "-w", "/volume", "-v", mount,
                   IMAGE, ".", "-type", "f").stdout  # fmt: skip
    return sorted(found.splitlines())


def remove(demo: Demo) -> None:
    """Delete the volumes of a demo.

    Args:
        demo: The demo.
    """
    docker("volume", "rm", "--force", *(demo.volume(kind) for kind in VOLUMES))
