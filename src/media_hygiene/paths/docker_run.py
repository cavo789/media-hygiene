r"""Write a `docker run` command the user can paste as is, in PowerShell or bash.

PowerShell continues a line with a backtick, bash with a backslash; both expand
`$HOME` inside double quotes, so a default host folder reads the same in both.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import ENV_PREFIX

if TYPE_CHECKING:
    from pathlib import Path

PUBLISHED_IMAGE: Final = "cavo789/media-hygiene"
# Set by a developer's build (Dockerfile target `local`): the image names itself.
IMAGE_VARIABLE: Final = f"{ENV_PREFIX}IMAGE"
TOOL_HOME: Final = "media-hygiene"  # folder of the user's home holding the tool folders
_WINDOWS_PATH = re.compile(r"^[A-Za-z]:\\")
_INDENT: Final = "  "
_BASH_USER: Final = '--user "$(id -u):$(id -g)"'  # new files belong to the user


class Shell(StrEnum):
    """The shell the command is written for."""

    POWERSHELL = "powershell"
    BASH = "bash"

    @property
    def continuation(self) -> str:
        """The end of a line continued on the next one.

        Returns:
            A backtick for PowerShell, a backslash for bash.
        """
        return " `" if self is Shell.POWERSHELL else " \\"

    def home_folder(self, name: str) -> str:
        r"""A folder of the tool in the user's home: the default for a missing mount.

        Args:
            name: The folder name, e.g. `journal`.

        Returns:
            `$HOME\media-hygiene\journal` or `$HOME/media-hygiene/journal`.
        """
        separator = "\\" if self is Shell.POWERSHELL else "/"
        return separator.join(("$HOME", TOOL_HOME, name))

    def make_folders(self, folders: tuple[str, ...]) -> str:
        """The command creating folders that may exist already.

        Args:
            folders: Host folders.

        Returns:
            `mkdir -Force …` (PowerShell) or `mkdir -p …` (bash).
        """
        flag = "-Force" if self is Shell.POWERSHELL else "-p"
        separator = ", " if self is Shell.POWERSHELL else " "
        return f"mkdir {flag} " + separator.join(f'"{folder}"' for folder in folders)


def running_image() -> str:
    """The image the suggested commands run: this one, as far as it can tell.

    A container cannot learn the name it was started under: a developer's build says
    it in `MEDIA_HYGIENE_IMAGE`, the published image leaves it unset.

    Returns:
        `MEDIA_HYGIENE_IMAGE` when set and not empty, `cavo789/media-hygiene` otherwise.
    """
    return os.environ.get(IMAGE_VARIABLE) or PUBLISHED_IMAGE


def guess_shell(hosts: tuple[str, ...]) -> Shell:
    r"""PowerShell when a host folder is a Windows path (`C:\…`), bash otherwise.

    Args:
        hosts: The host side of every volume.

    Returns:
        The shell.
    """
    if any(_WINDOWS_PATH.match(host) for host in hosts):
        return Shell.POWERSHELL
    return Shell.BASH


@dataclass(frozen=True, slots=True)
class Volume:
    """One `-v` option: a host folder (or named volume) on a mount point."""

    host: str
    point: Path
    read_only: bool = False

    def render(self) -> str:
        r"""The option, quoted for both shells.

        Returns:
            E.g. `-v "C:\Photos:/data/c/Photos:ro"`.
        """
        suffix = ":ro" if self.read_only else ""
        return f'-v "{self.host}:{self.point.as_posix()}{suffix}"'


@dataclass(frozen=True, slots=True)
class DockerRun:
    """Everything the command holds, rendered for one shell."""

    volumes: tuple[Volume, ...]
    options: tuple[str, ...]  # -e and -p options
    arguments: str  # the media-hygiene command and its options

    def render(self, shell: Shell) -> str:
        """Build the command, one option per line.

        Args:
            shell: The shell it is pasted into.

        Returns:
            The multi-line command.
        """
        user = (_BASH_USER,) if shell is Shell.BASH else ()
        lines = (
            "docker run --rm -it",
            *user,
            *(volume.render() for volume in self.volumes),
            *self.options,
            f"{running_image()} {self.arguments}",
        )
        head, *rest = lines
        body = [head, *(_INDENT + line for line in rest)]
        return (shell.continuation + "\n").join(body)
