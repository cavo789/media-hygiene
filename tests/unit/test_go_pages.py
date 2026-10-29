"""0397: the pages that sort a group checked on them are mounted writable by `mh`."""

from __future__ import annotations

from media_hygiene.cli.app import build_app
from media_hygiene.cli.safety import GO_PAGES, PHOTO_READERS, READ_ONLY_COMMANDS


def test_the_go_pages_are_writers_never_read_only() -> None:
    """Search and home: out of the `:ro` list, said apart."""
    names = {info.name for info in build_app().registered_commands}
    writers = {name for name in names if name not in READ_ONLY_COMMANDS}
    assert {"search", "home"} == GO_PAGES
    assert writers >= GO_PAGES
    assert not GO_PAGES & PHOTO_READERS


def test_browse_is_gone_without_an_alias() -> None:
    """0465: `browse` was the search on its folders; no command keeps the name."""
    names = {info.name for info in build_app().registered_commands}
    assert "browse" not in names
    assert "search" in names


def test_review_sort_is_gone() -> None:
    """0460: `review-sort` is an unknown command, no hidden alias."""
    names = {info.name for info in build_app().registered_commands}
    assert "review-sort" not in names
