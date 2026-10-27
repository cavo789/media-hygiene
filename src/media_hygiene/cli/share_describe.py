"""`share`: the question asked before the words of `tags` go into the copies (0381).

Yes by default (Enter accepts): the maintainer's choice. `--describe/--no-describe`
answers it for scripts and pages; without a terminal and without the option, Yes.
The model's sentence sometimes describes intimate scenes: that is why it is asked.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import typer

from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.console.output import Output


def describe_answer(
    output: Output,
    flag: bool | None,  # noqa: FBT001 - the option's own value
) -> Callable[[int], bool]:
    """The answer to give when photos of the album were described by `tags`.

    Args:
        output: Where to say the privacy line.
        flag: `--describe` (True), `--no-describe` (False), or neither (None).

    Returns:
        A function of the count of photos described, that answers.
    """

    def answer(count: int) -> bool:
        """Answer for this count of photos described.

        Args:
            count: The photos `tags` described.

        Returns:
            True to carry their words.
        """
        if flag is not None:
            return flag
        if not sys.stdin.isatty():
            return True
        output.info(
            _(
                "🔒 The sentence of the vision model sometimes describes intimate "
                "scenes; the names of people are never written."
            )
        )
        question = ngettext(
            "Add the description and the keywords found by tags to the copy of "
            "{n} photo?",
            "Add the description and the keywords found by tags to the copies of "
            "{n} photos?",
            count,
        ).format(n=count)
        return typer.confirm(question, default=True)

    return answer


def say_described(output: Output, described: int) -> None:
    """Say how many copies carry their words, read back from the disk.

    Args:
        output: Where to say it.
        described: The copies holding an XMP packet.
    """
    if described:
        output.info(
            ngettext(
                "🏷 {n} copy carries its description and keywords (read back).",
                "🏷 {n} copies carry their description and keywords (read back).",
                described,
            ).format(n=described)
        )
