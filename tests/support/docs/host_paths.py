r"""The reports' paths of a capture, as a Windows reader of the guides sees them (0196).

The generator keeps the reports in a Docker volume, never a folder of the maintainer's
own `C:`: the tool then prints the container's path, `/reports/<run>/report.html`. On
Windows, `mh` mounts `$HOME\media-hygiene\reports`, and the tool prints that folder.
"""

from __future__ import annotations

import re
from typing import Final

# The home of the guides' reader, as Windows writes it.
WINDOWS_REPORTS: Final = "C:\\Users\\you\\media-hygiene\\reports"
# A path below /reports, not the end of a `-v …:/reports` option.
_REPORT_PATH: Final = re.compile(r"(?<![\w:/])/reports/(\S+)")
_COLUMNS: Final = 80  # the width of the captures' terminal


def as_on_windows(screen: str) -> str:
    """Write the paths below /reports as the reader's Windows folder.

    Args:
        screen: A tidied capture, one terminal line per line.

    Returns:
        The capture; a line made longer than the terminal has its path on the next
        line, as Rich wraps it.
    """
    return "\n".join(_line(line) for line in screen.split("\n"))


def _line(line: str) -> str:
    """One line of a capture, its report path written for Windows.

    Args:
        line: The line.

    Returns:
        The line, or two when the path no longer fits after its label.
    """
    found = _REPORT_PATH.search(line)
    if found is None:
        return line
    path = WINDOWS_REPORTS + "\\" + found.group(1).replace("/", "\\")
    written = line[: found.start()] + path + line[found.end() :]
    if len(written) <= _COLUMNS or not line[: found.start()].strip():
        return written
    return line[: found.start()].rstrip() + "\n" + path + line[found.end() :]
