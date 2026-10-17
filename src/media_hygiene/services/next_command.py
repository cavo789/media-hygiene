"""The full `docker run` of the command that comes next, built from the mount table.

The user should not rebuild an eight-line command by hand: the folders of this run
come back on the same mount points (without `:ro` for a verb that changes them), the
tool folders it mounted too, and a tool folder the next verb needs but this run lacks
gets a default host folder in the user's home.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Final

from media_hygiene.config.windows_zones import WINDOWS_ZONE_VARIABLE
from media_hygiene.constants import ENV_PREFIX
from media_hygiene.i18n import _
from media_hygiene.paths.docker_run import (
    IMAGE_VARIABLE,
    DockerRun,
    Volume,
    guess_shell,
)
from media_hygiene.paths.host_folders import bind_source
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.quarantines import mounted_quarantines

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

TOOL_KINDS: Final = (
    MountKind.CONFIG,
    MountKind.CACHE,
    MountKind.REPORTS,
    MountKind.JOURNAL,
    MountKind.QUARANTINE,
)
CHANGING: Final = (MountKind.JOURNAL, MountKind.QUARANTINE)  # clean, undo, sort…
_NAMED_VOLUME = re.compile(r"/volumes/(?P<name>[^/]+)/_data$")
_TIMEZONE: Final = "TZ"
_PATH_SUFFIX: Final = "_DIR"  # MEDIA_HYGIENE_<NAME>_DIR: a mount point, not carried
# Set by the `mh` launcher (TODO 0060): the next command is then `mh <verb>`.
LAUNCHER_VARIABLE: Final = f"{ENV_PREFIX}LAUNCHER"
LAUNCHER_FUNCTION: Final = "mh"
# Set by an `mh` that runs the step chosen on the home page (exit code 100 + n, 0210).
LAUNCHER_STEPS_VARIABLE: Final = f"{LAUNCHER_VARIABLE}_STEPS"
# The image's own name is written in the command itself, not passed on with -e; `mh`
# reads the zone of the Windows host again at every run.
_NOT_CARRIED: Final = frozenset(
    {LAUNCHER_VARIABLE, LAUNCHER_STEPS_VARIABLE, IMAGE_VARIABLE, WINDOWS_ZONE_VARIABLE}
)


@dataclass(frozen=True, slots=True)
class NextVerb:
    """The command that comes next, and what it needs that an audit does not."""

    arguments: str  # e.g. "clean --prefer \"C:\\Photos\""
    needs: tuple[MountKind, ...] = ()  # tool folders it refuses to run without
    port: int | None = None  # a page served on this port


@dataclass(frozen=True, slots=True)
class NextCommand:
    """The command to paste, and the tool folders it adds with a default host path."""

    command: str
    added: tuple[MountKind, ...]

    def note(self) -> str:
        """Say which folders the command adds, so that nothing comes as a surprise.

        Returns:
            One sentence, or an empty string when the command adds nothing.
        """
        if not self.added:
            return ""
        points = ", ".join(f"/{kind.value}" for kind in self.added)
        return _("The command adds {points}: folders of your home.").format(
            points=points
        )


def next_command(runtime: Runtime, verb: NextVerb) -> NextCommand:
    """Build the `docker run` of `verb` with this run's folders and settings.

    Args:
        runtime: Settings, mount points and output.
        verb: The command that comes next.

    Returns:
        The command, for the shell guessed from the host folders; `mh <verb>`
        when the run was started by the launcher, which mounts everything.
    """
    if os.environ.get(LAUNCHER_VARIABLE):
        return NextCommand(f"{LAUNCHER_FUNCTION} {verb.arguments}", ())
    data = data_volumes(runtime, read_only=not set(verb.needs) & set(CHANGING))
    tools = {kind: tool_host(runtime, kind) for kind in TOOL_KINDS}
    shell = guess_shell(tuple(volume.host for volume in data))
    added = tuple(kind for kind in verb.needs if tools.get(kind) is None)
    for kind in added:
        tools[kind] = shell.home_folder(kind.value)
    drives = mounted_quarantines(runtime).drive_folders  # `/quarantine/e` (0183)
    volumes = (
        *data,
        *(
            Volume(host, runtime.locations.path_of(kind))
            for kind, host in tools.items()
            if host is not None
        ),
        *(Volume(host, at) for at in drives if (host := _host_of(runtime, at))),
    )
    port = () if verb.port is None else (f"-p 127.0.0.1:{verb.port}:{verb.port}",)
    run = DockerRun(volumes, (*environment(), *port), verb.arguments)
    command = run.render(shell)
    if added:
        folders = tuple(shell.home_folder(kind.value) for kind in added)
        command = shell.make_folders(folders) + "\n" + command
    return NextCommand(command, added)


def data_volumes(runtime: Runtime, *, read_only: bool) -> tuple[Volume, ...]:
    """The folders this run analysed, on the same mount points.

    Args:
        runtime: Settings, mount points and output.
        read_only: Mount them with `:ro`.

    Returns:
        One volume per data root.
    """
    roots = runtime.mounts.data_roots(runtime.locations.data_dir)
    to_host = runtime.mapper.to_host
    return tuple(
        Volume(bind_source(_host_of(runtime, root), to_host(root)), root, read_only)
        for root in roots
    )


def tool_host(runtime: Runtime, kind: MountKind) -> str | None:
    """The host folder (or named volume) behind a tool mount point of this run.

    Args:
        runtime: Settings, mount points and output.
        kind: Which mount point.

    Returns:
        Its host side, or None when this run did not mount it.
    """
    point = runtime.locations.path_of(kind)
    if point not in runtime.mounts.mount_points:
        return None
    return _host_of(runtime, point)


def _host_of(runtime: Runtime, point: Path) -> str | None:
    """What the mount table says is behind a mount point.

    Args:
        runtime: Settings, mount points and output.
        point: A mount point.

    Returns:
        The Windows folder, the name of a Docker volume or the host folder; None when
        the mount table does not tell.
    """
    windows = dict(runtime.mounts.host_sources).get(point)
    if windows is not None:
        return windows
    folder = dict(runtime.mounts.host_folders).get(point)
    if folder is None:
        return None
    path = str(PurePosixPath(*folder.parts))
    volume = _NAMED_VOLUME.search(path)
    return volume["name"] if volume is not None else path


def environment() -> tuple[str, ...]:
    """The `-e` options of this run worth keeping: the time zone, the settings.

    Returns:
        E.g. `-e TZ=Europe/Brussels`.
    """
    names = sorted(
        name
        for name in os.environ
        if name == _TIMEZONE
        or (
            name.startswith(ENV_PREFIX)
            and not name.endswith(_PATH_SUFFIX)
            and name not in _NOT_CARRIED
        )
    )
    return tuple(f'-e "{name}={os.environ[name]}"' for name in names)
