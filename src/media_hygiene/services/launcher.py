r"""The `mh` launcher: a shell function holding the mounts of one run, written once.

`docker run … launcher > mh.ps1` writes a PowerShell (or bash) function `mh` that runs
the image with the folders of that run: the photo folders read-only (`:ro`) unless the
command changes them, the tool folders always, a default folder of the user's home for
each tool folder the run lacked, and the port of the review pages for the commands
that serve one. `mh audit`, `mh clean`, `mh review` then replace the long commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.paths.docker_run import (
    Shell,
    Volume,
    guess_shell,
    running_image,
)
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.launcher_ascii import ascii_powershell
from media_hygiene.services.launcher_memory import locale_option
from media_hygiene.services.next_command import (
    LAUNCHER_FUNCTION,
    LAUNCHER_VARIABLE,
    TOOL_KINDS,
    data_volumes,
    environment,
    tool_host,
)

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

_TEMPLATE_PACKAGE: Final = "media_hygiene.cli"
_TEMPLATES: Final = {Shell.POWERSHELL: "mh.ps1.j2", Shell.BASH: "mh.sh.j2"}
SCRIPT_NAMES: Final = {Shell.POWERSHELL: "mh.ps1", Shell.BASH: "mh.sh"}
_PROFILES: Final = {Shell.POWERSHELL: "$PROFILE", Shell.BASH: "~/.bashrc"}
# The cache is a named volume (README), the other tool folders are in the home.
_CACHE_VOLUME: Final = "media-hygiene-cache"


@dataclass(frozen=True, slots=True)
class LauncherCommands:
    """Which commands exist, which change the photos, which serve a page."""

    names: tuple[str, ...]
    writers: tuple[str, ...]  # photos mounted read-write: no `:ro`
    pages: tuple[str, ...]  # `-p 127.0.0.1:<port>:<port>`
    data: tuple[str, ...]  # their output is redirected to a file: no terminal
    port: int


@dataclass(frozen=True, slots=True)
class LauncherScript:
    """Everything the script holds, rendered by the template of its shell."""

    shell: Shell
    data: tuple[Volume, ...]
    tools: tuple[Volume, ...]
    folders: str  # the host folders to create, quoted, for the shell
    environment: tuple[str, ...]
    commands: LauncherCommands


def launcher_script(
    runtime: Runtime, shell: Shell | None, commands: LauncherCommands
) -> LauncherScript:
    """Gather the folders of this run, and a default for each tool folder it lacks.

    Args:
        runtime: Settings, mount points and output.
        shell: The shell the script is for; None guesses it from the photo folders.
        commands: The commands of the CLI.

    Returns:
        The script, ready to render.
    """
    mounted = runtime.mounts.mount_points
    data = tuple(
        volume
        for volume in data_volumes(runtime, read_only=False)
        if volume.point in mounted
    )
    shell = shell or guess_shell(tuple(volume.host for volume in data))
    tools: list[Volume] = []
    created: list[str] = []
    for kind in TOOL_KINDS:
        host = tool_host(runtime, kind)
        if host is None and kind is MountKind.CACHE:
            host = _CACHE_VOLUME
        if host is None:
            host = shell.home_folder(kind.value)
            created.append(host)
        tools.append(Volume(host, runtime.locations.path_of(kind)))
    return LauncherScript(
        shell=shell,
        data=data,
        tools=tuple(tools),
        folders=_quoted(shell, tuple(created)),
        environment=(*environment(), *locale_option(runtime)),
        commands=commands,
    )


def render_script(script: LauncherScript) -> str:
    """Write the script, its header translated; `mh.ps1` in ASCII only.

    Args:
        script: What the script holds.

    Returns:
        The text of `mh.ps1` or `mh.sh`.
    """
    environment_ = translated_environment(_TEMPLATE_PACKAGE, escaped=())
    template = environment_.get_template(_TEMPLATES[script.shell])
    text = template.render(
        script=script,
        function=LAUNCHER_FUNCTION,
        variable=LAUNCHER_VARIABLE,
        image=running_image(),
        header=_header(script.shell),
    )
    return ascii_powershell(text) if script.shell is Shell.POWERSHELL else text


def script_path(shell: Shell) -> str:
    r"""Where the guides save the script: the tool folder of the user's home.

    Args:
        shell: The shell the script is for.

    Returns:
        `$HOME\media-hygiene\mh.ps1` or `$HOME/media-hygiene/mh.sh`.
    """
    return shell.home_folder(SCRIPT_NAMES[shell])


def load_command(shell: Shell) -> str:
    r"""The command loading the saved script into the current terminal.

    Args:
        shell: The shell the script is for.

    Returns:
        `. "$HOME\media-hygiene\mh.ps1"` or `source "$HOME/media-hygiene/mh.sh"`.
    """
    verb = "." if shell is Shell.POWERSHELL else "source"
    return f'{verb} "{script_path(shell)}"'


def _header(shell: Shell) -> tuple[str, ...]:
    """The comment lines opening the script: what it is, how to load it.

    Args:
        shell: The shell the script is for.

    Returns:
        Translated lines, without the comment sign.
    """
    load = load_command(shell)
    profile = _PROFILES[shell]
    return (
        _(
            "media-hygiene launcher: 'mh <command>' runs the tool on your folders, "
            "e.g. mh audit, then mh clean."
        ),
        _("Load it in this terminal with: {load}").format(load=load),
        _("For every terminal, add that line to {profile}.").format(profile=profile),
        _(
            "Another folder? Run 'launcher' again with one more -v, saving to the "
            "same file."
        ),
    )


def _quoted(shell: Shell, folders: tuple[str, ...]) -> str:
    """List folders as the shell takes them in one command.

    Args:
        shell: The shell.
        folders: Host folders.

    Returns:
        `"a", "b"` for PowerShell, `"a" "b"` for bash; empty without folders.
    """
    separator = ", " if shell is Shell.POWERSHELL else " "
    return separator.join(f'"{folder}"' for folder in folders)
