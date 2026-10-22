r"""What `mh share` needs: its fixed folder, mounted for this command only (0296).

The copies of an album to send go to `$HOME\media-hygiene\Shares` (`$HOME/...` for
bash), mounted on `/shares` when the command is `share`, never for another: no folder
typed each time, no photo folder written. `mh.ps1` then opens that folder in the
Explorer, where the album's folder and its zip are side by side.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.paths.locations import SHARES_POINT

if TYPE_CHECKING:
    from media_hygiene.paths.docker_run import Shell

SHARE_VERB: Final = "share"
SHARES_FOLDER: Final = "Shares"  # as the TODO and the docs name it in the Explorer
HELP_FLAGS: Final = ("--help", "-h")  # asked for the help: no folder opened


@dataclass(frozen=True, slots=True)
class ShareMount:
    """The verb, its folder on the host and its mount point in the container."""

    verb: str
    host: str
    point: str
    help_flags: tuple[str, ...] = HELP_FLAGS


def share_mount(shell: Shell) -> ShareMount:
    """The folder of `mh share` for a shell.

    Args:
        shell: The shell of the script.

    Returns:
        It, `$HOME` left for the shell to expand.
    """
    return ShareMount(
        SHARE_VERB, shell.home_folder(SHARES_FOLDER), SHARES_POINT.as_posix()
    )
