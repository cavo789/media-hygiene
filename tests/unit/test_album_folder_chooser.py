"""The albums' folder picked in the library's folders tree (0824): one component."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

from media_hygiene.search.album_root_desk import ALBUM_ROOT_FOLDERS
from media_hygiene.services.album_pages import album_edit_page, album_page
from tests.support.page_render import render_page

_SOURCES: Final = Path(__file__).parents[2] / "src" / "media_hygiene"


def test_the_albums_page_offers_the_librarys_tree_as_a_chooser() -> None:
    """The page draws the tree with the library's own `folder_tree.js.j2`."""
    page = album_page().decode()
    assert 'id="albumRootTree"' in page
    assert "window.mhPickFolder" in page
    assert "function folderBranch(" in page  # the library's tree, not a copy
    assert ALBUM_ROOT_FOLDERS in page
    assert 'id="albumRootField"' in page  # the typed field stays the fast path


# Every field where a host folder is typed (0850), by template: its 📂 button picks it
# in the tree. Found by grepping the `<input`s for a folder placeholder (`e.g. C:\…`).
_FOLDER_FIELDS: Final = {
    "share/templates/album_root_line.html.j2": "albumRootField",
    "share/templates/album_make.html.j2": "makeFolder",
    "search/templates/search_sort_setup.html.j2": "setupTarget",
}


def test_every_typed_folder_has_the_shared_picker() -> None:
    """Same 📂 button, same dialog: the shared chooser, wired by its data attributes."""
    found = {
        str(path.relative_to(_SOURCES)): path.read_text("utf-8")
        for path in _SOURCES.rglob("*.html.j2")
        if re.search(
            r"<input[^>]*placeholder=\"\{\{ _\('e\.g\. C:", path.read_text("utf-8")
        )
    }
    assert set(found) == set(_FOLDER_FIELDS)
    for name, field in _FOLDER_FIELDS.items():
        assert f'data-pick-field="{field}"' in found[name], name
        assert '{% include "folder_chooser.html.j2" %}' in found[name], name


def test_the_library_and_the_album_pages_carry_one_chooser() -> None:
    """The search page's sort setup and the album's make dialog: one dialog each."""
    for page in (album_edit_page().decode(), render_page("search.html.j2")):
        assert page.count('<dialog id="mhFolderPick"') == 1
        assert 'id="mhFolderPickTree"' in page
        assert "data-pick-field=" in page
