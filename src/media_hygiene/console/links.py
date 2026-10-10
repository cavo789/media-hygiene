r"""Host paths the user can open from the terminal: `C:\...` as a file hyperlink.

Rich writes the link as an OSC 8 sequence when the output is a terminal (`docker run
-it`): Windows Terminal opens it with Ctrl+click, other terminals show the plain path.
"""

from __future__ import annotations

from rich.markup import escape

from media_hygiene.paths.file_uri import file_uri


def file_link(host_path: str) -> str:
    r"""Render a host path as Rich markup, a hyperlink when it is a Windows path.

    Args:
        host_path: A path as the user knows it, such as `C:\Users\me\report.html`.

    Returns:
        The escaped path, wrapped in a `file:///` link when it is absolute on Windows.
    """
    text = escape(host_path)
    uri = file_uri(host_path)
    return text if uri is None else f"[link={uri}]{text}[/link]"
