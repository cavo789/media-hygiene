"""What follows a domain error on the console: its tip, a command, a page to read."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.errors import MediaHygieneError


def follow_up(output: Output, error: MediaHygieneError) -> None:
    """Print what follows an error: its tip, the command to paste, the page to read.

    Args:
        output: Where to print.
        error: The error, already printed.
    """
    if error.tip:
        output.tip(escape(error.tip))  # plain text: `[general]` is not markup
    if error.command:
        output.command(error.command)
    if error.link:
        output.link(*error.link)
