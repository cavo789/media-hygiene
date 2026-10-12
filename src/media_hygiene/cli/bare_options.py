"""`--decisions` given alone names the default file: `clean --decisions` is enough.

Typer has no option whose value may be left out, so the command line is completed
before it parses it: a `--decisions` that is last, or followed by another option, gets
`decisions.json`, the file `review` writes by default.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.review.place import DECISIONS_OPTION, DEFAULT_DECISIONS

if TYPE_CHECKING:
    from collections.abc import Sequence

_OPTION_MARK: Final = "-"


def with_default_decisions(arguments: Sequence[str]) -> list[str]:
    """Give a bare `--decisions` the default file.

    Args:
        arguments: The command line, without the program name.

    Returns:
        The same arguments, `decisions.json` added after a `--decisions` without value.
    """
    completed: list[str] = []
    for index, argument in enumerate(arguments):
        completed.append(argument)
        following = arguments[index + 1] if index + 1 < len(arguments) else None
        if argument == DECISIONS_OPTION and (
            following is None or following.startswith(_OPTION_MARK)
        ):
            completed.append(DEFAULT_DECISIONS)
    return completed
