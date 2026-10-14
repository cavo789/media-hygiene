"""The steps played in a browser: the burst review, `review --near`, `search`."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from tests.support.docs.container import Command, read_file, run
from tests.support.docs.screenshots import Job, shoot, start_review, stop_review

if TYPE_CHECKING:
    from pathlib import Path

    from tests.support.docs.container import Demo

PLACE: Final = "Parc du Cinquantenaire"  # a public park of Brussels

type Captures = dict[str, str]


def _serve(demo: Demo, args: tuple[str, ...], shots: Path) -> str:
    """Serve a page, let the browser shoot it, stop it.

    Args:
        demo: The demo library.
        args: The command, then the browser's mode and its arguments, split by `--`.
        shots: Where the screenshots land.

    Returns:
        What the page's terminal showed, tidied.
    """
    split = args.index("--")
    container = start_review(demo, args[:split])
    try:
        shoot(demo, Job(f"container:{container}", args[split + 1 :]), shots)
    finally:
        screen = stop_review(container)
    return screen


def served_pages(demo: Demo, shots: Path) -> Captures:
    """The burst review, then the near duplicates and the search.

    In the burst review, one shot is set aside in two series; nothing is decided in
    the near-duplicate review, so `clean` moves what the report shows.

    Args:
        demo: The demo library, audited.
        shots: Where the screenshots land (PNG).

    Returns:
        The terminals of the reviews and the decisions file.
    """
    captures = {"review.txt": _serve(demo, ("review", "--", "review"), shots)}
    captures["decisions.json"] = read_file(demo, "reports", "decisions.json")
    near = ("review", "--near", "--", "near")
    captures["review-near.txt"] = _serve(demo, near, shots)
    # The words of the folders and dates: no vision model in the documentation.
    run(demo, Command(("tags", "--no-describe")))
    word = demo.library.names.birthday.rsplit("/", maxsplit=1)[-1].casefold()
    _serve(demo, ("search", "--", "search", word), shots)
    return captures


def places_story(demo: Demo, shots: Path) -> None:
    """Name the park on the places map; the place stays in config.toml, unread.

    Args:
        demo: The demo library, audited: its cache holds the GPS positions.
        shots: Where the screenshots land (PNG).
    """
    container = start_review(demo, ("places",))
    try:
        shoot(demo, Job(f"container:{container}", ("places", PLACE)), shots)
    finally:
        stop_review(container)
