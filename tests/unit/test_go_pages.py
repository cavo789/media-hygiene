"""0397: the pages that sort a group checked on them are mounted writable by `mh`."""

from __future__ import annotations

from media_hygiene.cli.app import build_app
from media_hygiene.cli.safety import GO_PAGES, PHOTO_READERS, READ_ONLY_COMMANDS


def test_the_go_pages_are_writers_never_read_only() -> None:
    """review-sort, browse, search and home: out of the `:ro` list, said apart."""
    names = {info.name for info in build_app().registered_commands}
    writers = {name for name in names if name not in READ_ONLY_COMMANDS}
    assert {"review-sort", "browse", "search", "home"} == GO_PAGES
    assert writers >= GO_PAGES
    assert not GO_PAGES & PHOTO_READERS
