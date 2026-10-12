"""Refuse a question that no one could answer: no interactive terminal."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from typing import TextIO


def require_terminal(stdin: TextIO) -> None:
    """Refuse to ask a question without a terminal to answer it in.

    Args:
        stdin: The standard input.

    Raises:
        MediaHygieneError: There is no interactive terminal.
    """
    if not stdin.isatty():
        raise MediaHygieneError(
            _("Cannot ask for confirmation without an interactive terminal."),
            _("Run docker with -it, or add --yes."),
        )
