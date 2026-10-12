r"""`file:///` addresses of host paths, for terminal links and report pages.

Only an absolute Windows path (`C:\Photos\a.mp4`) has one: inside the container, the
host folder behind a mount point may be unknown, and then nothing can be opened.
"""

from __future__ import annotations

from pathlib import PureWindowsPath
from typing import Final
from urllib.parse import quote

_FILE_SCHEME: Final = "file:///"
_URI_SAFE: Final = "/:"


def file_uri(host_path: str) -> str | None:
    r"""The address a browser or Windows opens a host file with.

    Args:
        host_path: A path as the user knows it, such as `C:\Photos\a.mp4`.

    Returns:
        The `file:///C:/Photos/a.mp4` address, None when the path is not absolute on
        Windows.
    """
    windows = PureWindowsPath(host_path)
    if not windows.is_absolute():
        return None
    return _FILE_SCHEME + quote(windows.as_posix(), safe=_URI_SAFE)
