"""The settings of a server of the whole session, read again when their files change.

A command reads `config.toml` and `/config/people/*.toml` when it starts, then lives a
few minutes. The home server lives the whole session (0355, 0356) while the user edits
`config.toml`, names a person on the people page or saves a place, each in a container
of its own: without this it would show stale settings until `mh` starts again (0358).
The files are compared by content (a few KB, SHA-256): a copy keeping the old mtime,
an atomic save (another inode), an edit in place or a removal are all seen alike. A
file that no longer loads keeps the last good settings, said once in the console.
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

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime

# The files read at most once a second: a page asks a dozen times when it opens, and
# Docker Desktop's file sharing makes each read of /config slower than on Linux (0277).
CHECK_SECONDS: Final = 1.0


def settings_mark(locations: Locations) -> bytes:
    """A digest of every file the settings are read from.

    Args:
        locations: The mount points: `config.toml` and its `people` folder.

    Returns:
        The digest; another one as soon as a file is added, removed or changed.
    """
    digest = hashlib.sha256()
    files = (locations.config_file, *sorted((locations.config_dir / FOLDER).glob("*")))
    for path in files:
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
        self._every = every
        self._checked = time.monotonic()

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
            return self._runtime
        self._runtime = replace(self._runtime, loaded=loaded)
        return self._runtime
