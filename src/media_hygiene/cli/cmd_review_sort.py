"""`media-hygiene review-sort`: the search's *🗂 Events* view, one more version (0439).

Review-sort's page is gone: its events, choices and rules are the search page's *🗂
Events* view (`/events`, 0437, 0438). The verb opens that view, says so in one line, and
goes in the next version. `sort-decisions.json` is written as before.
"""

# pylint: disable=import-outside-toplevel  # lazy: a command loads its code when it runs

from __future__ import annotations

from typing import Annotated

import typer

from media_hygiene.cli import review_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.i18n import _


def review_sort_command(
    ctx: typer.Context,
    *,
    port: Annotated[int | None, review_options.port()] = None,
) -> None:
    """Open the search's Events view of the latest classify run, until Ctrl+C.

    Args:
        ctx: Typer context holding the runtime.
        port: `--port`, inside the container.
    """
    from media_hygiene.cli.next_steps import carried, suggest
    from media_hygiene.search.events_desk import EVENTS_PAGE_PATH
    from media_hygiene.services.next_command import CHANGING, NextVerb
    from media_hygiene.services.search import open_search
    from media_hygiene.services.search_pages import PageStart, serve_pages

    runtime = runtime_of(ctx)
    port = review_options.page_port(runtime, port)
    output = runtime.output
    output.warning(
        _(
            "'review-sort' now opens the 🗂 Events view of 'search', and goes in the "
            "next version: use 'search'."
        )
    )
    ready = _(
        "The events of the latest classify run are ready, open {url} in your "
        "browser. Each choice is saved at once in sort-decisions.json. Ctrl+C stops it."
    )
    with user_errors(output), open_search(runtime, words=False) as search:
        start = PageStart(port, EVENTS_PAGE_PATH, ready, None, EVENTS_PAGE_PATH[1:])
        serve_pages(runtime, search, start)
        output.blank()
        suggest(
            runtime,
            _(
                "'sort' applies them on top of the workbook, which you may still "
                "edit; it refuses an event or a file edited otherwise in both."
            ),
            NextVerb(carried(runtime, "sort"), CHANGING),
        )
