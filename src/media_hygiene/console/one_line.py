"""Messages for a stream that is not a terminal (`docker run` without `-t`, 0541).

Rich would break a message at an assumed width: real line breaks, which the host window
then shows whatever its own width. There, a message stays one line and the window wraps
it. Tables and panels do need a width: the host's `COLUMNS`, else `TABLE_WIDTH`.
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Final

from rich.text import Text

if TYPE_CHECKING:
    from rich.console import Console, RenderableType

TABLE_WIDTH: Final = 120


def say(console: Console, message: RenderableType) -> None:
    """Print a message, on one line unless a terminal is there to fit it.

    The stream itself decides: `--color always` makes Rich call any stream a terminal.

    Args:
        console: Where to print.
        message: Text is kept on one line; a table or a panel keeps the console's width.
    """
    is_text = isinstance(message, str | Text)
    console.print(message, soft_wrap=is_text and not console.file.isatty())


def width_without_terminal() -> int | None:
    """The width to impose on a console, when nothing tells the real one.

    Returns:
        None when `COLUMNS` or a terminal gives it (Rich reads both), else the default.
    """
    columns = os.environ.get("COLUMNS", "")
    if columns.isdigit() and int(columns) > 0:
        return None
    return None if _has_terminal() else TABLE_WIDTH


def _has_terminal() -> bool:
    """Whether a standard stream reports a size, the way Rich looks for one.

    Returns:
        True when one of stdin, stdout and stderr is a terminal.
    """
    return any(stream.isatty() for stream in (sys.stdin, sys.stdout, sys.stderr))
