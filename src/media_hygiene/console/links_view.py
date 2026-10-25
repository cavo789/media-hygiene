"""Show what `sort` or `undo` did to the user's files naming photos (0382)."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.services.sort_links import LinksFollowed


def show_links(output: Output, links: LinksFollowed) -> None:
    """One line for the files rewritten and read back, a warning per problem.

    Args:
        output: The console.
        links: What the run did to them.
    """
    for line in links.lines:
        output.info(line)
    for problem in links.problems:
        output.warning(problem)
