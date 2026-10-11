"""The SQL of the search: the full-text table, built from `tags`, and its queries.

The table lives in the connection's `temp` schema: it is rebuilt from the tags (one
row per file, one column per source) when the index changed, and never written into
the index file, which is opened read-only. Every name comes from `TagSource`, never
from input.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.search.query import match_expression
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    from media_hygiene.search.query import SearchQuery

TABLE: Final = "search_text"
_COLUMNS: Final = tuple(source.value for source in TagSource)
# Between two tags of a column: punctuation, never a word.
_SEPARATOR: Final = " ; "
# `remove_diacritics 2`: "noel" finds "Noël", "cafe" finds "café".
CREATE: Final = (
    f"CREATE VIRTUAL TABLE temp.{TABLE} USING fts5({', '.join(_COLUMNS)},"
    " tokenize = 'unicode61 remove_diacritics 2')"
)
DROP: Final = f"DROP TABLE IF EXISTS temp.{TABLE}"
_CONCATENATED: Final = ", ".join(
    f"group_concat(CASE WHEN t.source = '{name}' THEN t.value END, '{_SEPARATOR}')"
    for name in _COLUMNS
)
# Only the tags of the version of each file the index knows.
FILL: Final = (
    f"INSERT INTO temp.{TABLE} (rowid, {', '.join(_COLUMNS)})"  # noqa: S608
    f" SELECT f.rowid, {_CONCATENATED} FROM tags AS t JOIN files AS f"
    " ON f.path = t.path AND f.size = t.size AND f.mtime_ns = t.mtime_ns"
    " GROUP BY f.rowid"
)
DATA_VERSION: Final = "PRAGMA data_version"
HAS_TAGS: Final = "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'tags'"
_FROM: Final = f" FROM temp.{TABLE} JOIN files ON files.rowid = {TABLE}.rowid"
HITS: Final = (
    "SELECT files.rowid, files.path, files.size, files.mtime_ns, files.media_date"
    + _FROM
)
COUNT: Final = "SELECT COUNT(*)" + _FROM
MATCHES: Final = f"{TABLE} MATCH ?"
YEARS: Final = "CAST(substr(files.media_date, 1, 4) AS INTEGER) BETWEEN ? AND ?"
# `fold` is Python's `casefold`: SQLite's `lower` knows ASCII only.
FOLD: Final = "fold"
FOLDER: Final = f"instr({FOLD}(files.path), ?) > 0"
BEST_FIRST: Final = f" ORDER BY {TABLE}.rank"
# EXIF writes `2019:07:14`, videos `2019-07-14T…`: compared as one format.
NEWEST_FIRST: Final = (
    " ORDER BY replace(substr(files.media_date, 1, 10), ':', '-') DESC, files.path"
)
LIMIT: Final = " LIMIT ?"
WHERE: Final = " WHERE "
AND: Final = " AND "
SOURCE_OF: Final = "SELECT path, size, mtime_ns FROM files WHERE rowid = ?"


def conditions(query: SearchQuery) -> tuple[list[str], list[object]]:
    """The conditions of a search, and their parameters.

    Args:
        query: Its words and filters.

    Returns:
        The SQL conditions (constant fragments) and their values, in order.
    """
    chosen: list[str] = []
    parameters: list[object] = []
    expression = match_expression(query)
    if expression is not None:
        chosen.append(MATCHES)
        parameters.append(expression)
    filters = query.filters
    if filters.years is not None:
        chosen.append(YEARS)
        parameters.extend(filters.years)
    folder = filters.folder.strip().replace("\\", "/").casefold()
    if folder:
        chosen.append(FOLDER)
        parameters.append(folder)
    return chosen, parameters
