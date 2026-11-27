"""The albums' folder picked in the library's folders tree (0824): one component."""

from __future__ import annotations

from media_hygiene.search.album_root_desk import ALBUM_ROOT_FOLDERS
from media_hygiene.services.album_pages import album_page


def test_the_albums_page_offers_the_librarys_tree_as_a_chooser() -> None:
    """The page draws the tree with the library's own `folder_tree.js.j2`."""
    page = album_page().decode()
    assert 'id="albumRootTree"' in page
    assert "window.mhPickFolder" in page
    assert "function folderBranch(" in page  # the library's tree, not a copy
    assert ALBUM_ROOT_FOLDERS in page
    assert 'id="albumRootField"' in page  # the typed field stays the fast path
