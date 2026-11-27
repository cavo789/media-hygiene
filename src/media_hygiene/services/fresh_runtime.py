"""The settings of a server of the whole session, read again when their files change.

A command reads `config.toml` and `/config/people/*.toml` when it starts, then lives a
few minutes. The home server lives the whole session (0355, 0356) while the user edits
`config.toml`, names a person on the people page or saves a place, each in a container
of its own: without this it would show stale settings until `mh` starts again (0358).
The files are compared by content (SHA-256), once their stamps say something may
have changed: a copy keeping the old mtime (its ctime), an atomic save (another
inode), an edit in place or a removal are all seen alike, and a file saved again
unchanged reloads nothing. Only the stamps are read each second: the people's files
reached 1.2 MB, read in 0.8 s over Docker Desktop's file sharing (2026-11-16). A
file that no longer loads keeps the last good settings, said once in the console and,
until it loads again, on the pages (`error`, 0364): the server runs in the background.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import replace
from typing import TYPE_CHECKING, Final

from media_hygiene.config.loader import load_settings
from media_hygiene.config.people_files import FOLDER
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.next_command import tool_host

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime

# The files read at most once a second: a page asks a dozen times when it opens, and
# Docker Desktop's file sharing makes each read of /config slower than on Linux (0277).
CHECK_SECONDS: Final = 1.0


def settings_stamps(locations: Locations) -> tuple[tuple[object, ...], ...]:
    """The stamp of every file the settings are read from, without reading them.

    Args:
        locations: The mount points: `config.toml` and its `people` folder.

    Returns:
        Each file's name, inode, size, modification and change times.
    """
    stamps: list[tuple[object, ...]] = []
    for path in _settings_files(locations):
        try:
            status = path.stat()
        except OSError:
            stamps.append((path.name,))
            continue
        times = (status.st_mtime_ns, status.st_ctime_ns)
        stamps.append((path.name, status.st_ino, status.st_size, *times))
    return tuple(stamps)


def _settings_files(locations: Locations) -> tuple[Path, ...]:
    """`config.toml` and the files of its `people` folder.

    Args:
        locations: The mount points.

    Returns:
        The files, in order.
    """
    return (locations.config_file, *sorted((locations.config_dir / FOLDER).glob("*")))


def settings_mark(locations: Locations) -> bytes:
    """A digest of every file the settings are read from.

    Args:
        locations: The mount points: `config.toml` and its `people` folder.

    Returns:
        The digest; another one as soon as a file is added, removed or changed.
    """
    digest = hashlib.sha256()
    for path in _settings_files(locations):
        digest.update(path.name.encode())
        try:
            digest.update(path.read_bytes())
        except OSError:  # gone, or a folder: its absence is part of the mark
            digest.update(b"\0")
    return digest.digest()


class FreshRuntime:
    """The runtime of a long-lived server, its settings loaded again when changed."""

    def __init__(self, runtime: Runtime, every: float = CHECK_SECONDS) -> None:
        """Start from the runtime the server was started with.

        Args:
            runtime: Its settings, mount points and output.
            every: Seconds between two reads of the files, at least.
        """
        self._runtime = runtime
        self._mark = settings_mark(runtime.locations)
        self._stamps = settings_stamps(runtime.locations)
        self._every = every
        self._checked = time.monotonic()
        self._error = ""

    @property
    def error(self) -> str:
        """What the pages say while a settings file does not load.

        Returns:
            One translated line naming the file as Explorer shows it; empty once the
            files load.
        """
        return self._error

    def runtime(self) -> Runtime:
        """The runtime with the settings the files hold now.

        Returns:
            The same object while nothing changed; a new one once a file changed
            and loads; the last good one when it does not.
        """
        now = time.monotonic()
        if now - self._checked < self._every:
            return self._runtime
        self._checked = now
        stamps = settings_stamps(self._runtime.locations)
        if stamps == self._stamps:
            return self._runtime
        self._stamps = stamps
        mark = settings_mark(self._runtime.locations)
        if mark == self._mark:
            return self._runtime
        self._mark = mark
        try:
            loaded = load_settings(self._runtime.locations, self._runtime.cli_layer)
        except ConfigError as error:
            self._runtime.output.warning(
                _(
                    "The settings changed but cannot be read; the last good ones stay: "
                    "{error}"
                ).format(error=error.message)
            )
            self._error = _(
                "{file} cannot be read: {error}. The last good settings stay until it "
                "is fixed."
            ).format(file=_shown(self._runtime), error=error.message)
            return self._runtime
        self._error = ""
        self._runtime = replace(self._runtime, loaded=loaded)
        return self._runtime


def _shown(runtime: Runtime) -> str:
    """`config.toml` as Explorer shows it, when the mount table tells.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        Its Windows path, else its path in the container.
    """
    file = runtime.locations.config_file
    host = tool_host(runtime, MountKind.CONFIG)
    return f"{host.rstrip(chr(92))}\\{file.name}" if host else str(file)
