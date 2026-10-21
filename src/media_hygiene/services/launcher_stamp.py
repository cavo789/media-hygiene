"""`mh` saying that its own file was written by another build of the image (0290).

`mh.ps1` and `mh.sh` live on the host: pulling a new image (Docker Desktop, `docker
pull`) or building one locally leaves them as an older image wrote them, and what they
do (the step codes of home, the window of a long run) then disagrees with the image.
The script carries the stamp of the image that wrote it and passes it with `-e` to
every run; the image compares it with its own, for free (no docker call, no stat):
when they differ, or when the script passes none (written before this check existed),
one line names `mh update`, which writes the file again with the same folders, pulled
or not.

The stamp is the version and the start of the SHA-256 of the installed wheel's `RECORD`,
which lists the digest of every file of the package: a local build of the same version
with other code gets another stamp; the same code built twice keeps it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, distribution
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.services.next_command import LAUNCHER_FUNCTION, LAUNCHER_VARIABLE

if TYPE_CHECKING:
    from collections.abc import Mapping

# Set by `mh` at each run: the stamp of the image that wrote it.
LAUNCHER_STAMP_VARIABLE: Final = f"{LAUNCHER_VARIABLE}_STAMP"
_DISTRIBUTION: Final = "media-hygiene"
_DIGITS: Final = 12  # of the digest: enough to tell two builds apart
_BUILD: Final = "+"


@dataclass(frozen=True, slots=True)
class LauncherStamp:
    """What the script passes to each run: the variable and the stamp of its image."""

    variable: str
    value: str


def image_stamp() -> str:
    """The stamp of this image: its version, then the digest of its installed files.

    Returns:
        E.g. `0.4.0+1a2b3c4d5e6f`; the version alone without a `RECORD`; empty when
        the package is not installed (no line is ever said then).
    """
    try:
        installed = distribution(_DISTRIBUTION)
    except PackageNotFoundError:
        return ""
    record = installed.read_text("RECORD")
    if not record:
        return installed.version
    digest = sha256(record.encode()).hexdigest()[:_DIGITS]
    return f"{installed.version}{_BUILD}{digest}"


def launcher_stamp() -> LauncherStamp:
    """The stamp `launcher` writes into the script.

    Returns:
        The variable and this image's stamp.
    """
    return LauncherStamp(LAUNCHER_STAMP_VARIABLE, image_stamp())


def stamp_line(environ: Mapping[str, str], stamp: str) -> str:
    """The line said when the `mh` running this command was written by another image.

    Args:
        environ: The environment of this run (`os.environ`).
        stamp: This image's stamp.

    Returns:
        The line; empty when not run by `mh`, when the stamps agree, or when this
        image has no stamp.
    """
    if not environ.get(LAUNCHER_VARIABLE) or not stamp:
        return ""
    written = environ.get(LAUNCHER_STAMP_VARIABLE, "")
    if written == stamp:
        return ""
    if not written:
        text = _(
            "This {command} was written by an older image than {image}: type "
            "{command} update to write it again, with the same folders."
        )
    else:
        text = _(
            "This {command} was written by the image {written}, this one is {image}: "
            "type {command} update to write it again, with the same folders."
        )
    return text.format(
        command=LAUNCHER_FUNCTION, image=_shown(stamp), written=_shown(written)
    )


def say_stamp(environ: Mapping[str, str] | None = None) -> str:
    """The line for this run, from the real environment and this image's stamp.

    Args:
        environ: The environment; None reads `os.environ`.

    Returns:
        The line, or empty.
    """
    return stamp_line(os.environ if environ is None else environ, image_stamp())


def _shown(stamp: str) -> str:
    """A stamp as people read it: `0.4.0 (build 1a2b3c4d5e6f)`.

    Args:
        stamp: A stamp, the build part optional.

    Returns:
        The version, then its build between brackets when there is one.
    """
    version, _plus, build = stamp.partition(_BUILD)
    if not build:
        return version
    return _("{version} (build {build})").format(version=version, build=build)
