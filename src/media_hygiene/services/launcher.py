r"""The `mh` launcher: a shell function holding the mounts of one run, written once.

`docker run … launcher > mh.ps1` writes a PowerShell (or bash) function `mh` that runs
the image with the folders of that run: the photo folders read-only (`:ro`) unless the
command changes them, the tool folders always, a default folder of the user's home for
each tool folder the run lacked, a quarantine on each photo drive (0183,
`launcher_drives.py`), and the port of the review pages for the commands
that serve one. `mh audit`, `mh clean`, `mh review` then replace the long commands.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.config.windows_zones import WINDOWS_ZONE_VARIABLE
from media_hygiene.constants import ExitCode
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.paths.docker_run import Shell, Volume, guess_shell, running_image
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.home_fields import RELAY_FIELDS
from media_hygiene.review.home_views import (
    FIELDS_STEP,
    SIGNAL_EXIT_BASE,
    STEP_EXIT_BASE,
)
from media_hygiene.services.launcher_ascii import ascii_powershell
from media_hygiene.services.launcher_backup import backup_command
from media_hygiene.services.launcher_cloud import cloud_check
from media_hygiene.services.launcher_drives import with_drive_quarantines
from media_hygiene.services.launcher_file import header
from media_hygiene.services.launcher_folders import checked_folders
from media_hygiene.services.launcher_guards import launcher_guards
from media_hygiene.services.launcher_host import host_commands
from media_hygiene.services.launcher_kept import CACHE_VOLUME, kept_run
from media_hygiene.services.launcher_launch import launch_texts
from media_hygiene.services.launcher_memory import locale_option
from media_hygiene.services.launcher_menu import (
    BROWSE_WAIT,
    DESKTOP_WAIT,
    menu_texts,
)
from media_hygiene.services.launcher_nas import SMB_OPTIONS, NasShare, nas_texts
from media_hygiene.services.launcher_phone import phone_command
from media_hygiene.services.launcher_stale import stale_texts
from media_hygiene.services.launcher_stamp import launcher_stamp
from media_hygiene.services.launcher_update import update_texts
from media_hygiene.services.next_command import (
    LAUNCHER_FUNCTION,
    LAUNCHER_PHOTOS_VARIABLE,
    LAUNCHER_STEPS_VARIABLE,
    LAUNCHER_VARIABLE,
    TOOL_KINDS,
    data_volumes,
    environment,
    tool_host,
)

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

_TEMPLATE_PACKAGE: Final = "media_hygiene.cli"
# The pages that may end on a step `mh` runs: the home page, browse's Apply now (0243);
# any other page opened from home gets the relay too: its way back home (0280).
_RELAYED: Final = ("home", "browse")
_TEMPLATES: Final = {Shell.POWERSHELL: "mh.ps1.j2", Shell.BASH: "mh.sh.j2"}


@dataclass(frozen=True, slots=True)
class LauncherCommands:  # pylint: disable=too-many-instance-attributes  # one per role
    """Which commands exist, which change the photos, which serve a page."""

    names: tuple[str, ...]
    writers: tuple[str, ...]  # photos mounted read-write: no `:ro`
    pages: tuple[str, ...]  # `-p 127.0.0.1:<port>:<port>`
    data: tuple[str, ...]  # their output is read or redirected: no terminal, no input
    port: int
    long: tuple[str, ...] = ()  # the computer kept awake, the end told (0179, 0185)
    backups: tuple[str, ...] = ()  # they take `--backup`: given each backup (0205)
    browse_wait: int = BROWSE_WAIT  # seconds `mh` waits for a page before giving up


@dataclass(frozen=True, slots=True)
class LauncherScript:  # pylint: disable=too-many-instance-attributes
    """Everything the script holds, rendered by the template of its shell."""

    shell: Shell
    data: tuple[Volume, ...]
    tools: tuple[Volume, ...]
    created: tuple[str, ...]  # the host folders `mh` creates
    environment: tuple[str, ...]
    commands: LauncherCommands
    data_dir: Path  # where `--photos` folders are mounted (`/data`)
    drives: tuple[Volume, ...] = ()  # `/quarantine/e`: each drive's own (0183)
    backups: tuple[Volume, ...] = ()  # compared, never changed: always `:ro` (0205)
    nas: tuple[NasShare, ...] = ()  # backups on a NAS: a Docker volume each (0245)

    @property
    def folders(self) -> str:
        """The folders to create, as the shell takes them in one command.

        Returns:
            `"a", "b"` for PowerShell, `"a" "b"` for bash; empty without folders.
        """
        separator = ", " if self.shell is Shell.POWERSHELL else " "
        return separator.join(f'"{folder}"' for folder in self.created)


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
            host = CACHE_VOLUME
        if host is None:
            host = shell.home_folder(kind.value)
            created.append(host)
        tools.append(Volume(host, runtime.locations.path_of(kind)))
    return LauncherScript(
        shell=shell,
        data=data,
        tools=tuple(tools),
        created=tuple(created),
        environment=(*environment(), *locale_option(runtime)),
        commands=commands,
        data_dir=runtime.locations.data_dir,
    )


def render_script(script: LauncherScript) -> str:
    """Write the script, its header translated; `mh.ps1` in ASCII only.

    Args:
        script: What the script holds.

    Returns:
        The text of `mh.ps1` or `mh.sh`.
    """
    script = with_drive_quarantines(script)
    environment_ = translated_environment(_TEMPLATE_PACKAGE, escaped=())
    template = environment_.get_template(_TEMPLATES[script.shell])
    text = template.render(
        script=script,
        function=LAUNCHER_FUNCTION,
        variable=LAUNCHER_VARIABLE,
        image=running_image(),
        header=header(script.shell),
        texts=menu_texts(),
        guards=launcher_guards(),
        desktop_wait=DESKTOP_WAIT,
        kept=kept_run(script),
        update=update_texts(),
        stale=stale_texts(),
        stamp=launcher_stamp(),
        host=host_commands(script),
        launch=launch_texts(),
        checked=(
            *checked_folders(script),
            *(volume.host for volume in script.backups),
        ),
        cloud=cloud_check(script.commands.names),
        phone=phone_command(),
        backup=backup_command(),
        zone=WINDOWS_ZONE_VARIABLE,
        relay=LAUNCHER_STEPS_VARIABLE,
        relay_fields=RELAY_FIELDS,
        photos=LAUNCHER_PHOTOS_VARIABLE,
        relayed=tuple(dict.fromkeys((*_RELAYED, *script.commands.pages))),
        step_base=STEP_EXIT_BASE,
        fields_code=STEP_EXIT_BASE + FIELDS_STEP,
        signal_base=SIGNAL_EXIT_BASE,
        page_closed=int(ExitCode.PAGE_CLOSED),
        nas=nas_texts(),
        smb=SMB_OPTIONS,
    )
    return ascii_powershell(text) if script.shell is Shell.POWERSHELL else text
