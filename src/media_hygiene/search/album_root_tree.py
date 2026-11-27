"""The folders tree offered to choose the albums' folder (0824).

The same tree as the library's folder view (`folder_tree`: `GET /api/folders`), read
from the index file alone: the albums page has no search index open. The page draws it
with the library's own `folder_tree.js.j2`.
"""

from __future__ import annotations

import sqlite3
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.index.read_only import connect_read_only
from media_hygiene.review.serving import json_response
from media_hygiene.search import statements as sql
from media_hygiene.search.folder_tree import folder_counts, listed_tree

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.review.http import Response


def folders_response(
    index_file: Path | None, mapper: HostPathMapper, roots: tuple[Path, ...]
) -> Response:
    """`GET /api/album-root/folders`: the folders of the index under the mounted ones.

    Args:
        index_file: The index, if any.
        mapper: Container paths to the host's.
        roots: The mounted folders, in the container.

    Returns:
        `{"folders": [...]}` as the library's tree sends it; empty without an index.
    """
    if index_file is None or not index_file.is_file():
        return json_response(HTTPStatus.OK, {"folders": []})
    try:
        connection = connect_read_only(index_file)
        try:
            rows = connection.execute(sql.ALL_FILES).fetchall()
        finally:
            connection.close()
    except sqlite3.Error:
        return json_response(HTTPStatus.OK, {"folders": []})
    folders = listed_tree(folder_counts(rows, roots), mapper, roots)
    return json_response(HTTPStatus.OK, {"folders": folders})
