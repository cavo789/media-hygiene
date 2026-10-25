"""The SQL of the search: the full-text table, built from `tags`, and its queries.

The table lives in the connection's `temp` schema: it is rebuilt from the tags (one
row per file, one column per source) when the index changed, and never written into
the index file, which is opened read-only. Every name comes from `TagSource`, never
from input.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.search.days import NAME as DAY
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
PEOPLE: Final = "person_words"
# The names of the people on each photo, made at each search: never in the index file.
CREATE_PEOPLE: Final = (
    f"CREATE TEMP TABLE IF NOT EXISTS {PEOPLE}"
    " (path TEXT NOT NULL, value TEXT NOT NULL)"
)
PUT_PERSON: Final = "INSERT INTO temp.person_words (path, value) VALUES (?, ?)"
CLEAR_PEOPLE: Final = "DELETE FROM temp.person_words"  # named again: one name less
_TAG_ROWS: Final = "SELECT path, size, mtime_ns, source, value FROM tags"
_PERSON_ROWS: Final = (
    "SELECT p.path AS path, w.size AS size, w.mtime_ns AS mtime_ns,"  # noqa: S608
    f" '{TagSource.PERSON.value}' AS source, p.value AS value"
    f" FROM temp.{PEOPLE} AS p JOIN files AS w ON w.path = p.path"
)
# Only the tags of the version of each file the index knows.
_FILL: Final = (
    f"INSERT INTO temp.{TABLE} (rowid, {', '.join(_COLUMNS)})"  # noqa: S608
    f" SELECT f.rowid, {_CONCATENATED} FROM ({{rows}}) AS t JOIN files AS f"
    " ON f.path = t.path AND f.size = t.size AND f.mtime_ns = t.mtime_ns"
    " GROUP BY f.rowid"
)
FILL: Final = _FILL.format(rows=f"{_TAG_ROWS} UNION ALL {_PERSON_ROWS}")
FILL_PEOPLE: Final = _FILL.format(rows=_PERSON_ROWS)  # an index without tags yet
DATA_VERSION: Final = "PRAGMA data_version"
HAS_TAGS: Final = "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'tags'"
ANY_TAG: Final = "SELECT 1 FROM tags LIMIT 1"  # at least one file has a word
_FROM: Final = f" FROM temp.{TABLE} JOIN files ON files.rowid = {TABLE}.rowid"
HITS: Final = (
    "SELECT files.rowid, files.path, files.size, files.mtime_ns,"
    f" {DAY}(files.media_date)" + _FROM
)
COUNT: Final = "SELECT COUNT(*)" + _FROM
MATCHES: Final = f"{TABLE} MATCH ?"
# `media_day` reads every form a date is written in (`search/days.py`).
YEARS: Final = f"CAST(substr({DAY}(files.media_date), 1, 4) AS INTEGER) BETWEEN ? AND ?"
# `fold` is Python's `casefold`: SQLite's `lower` knows ASCII only.
FOLD: Final = "fold"
FOLDER: Final = f"instr({FOLD}(files.path), ?) > 0"
BEST_FIRST: Final = f" ORDER BY {TABLE}.rank"
# EXIF writes `2019:07:14` or `14/07/2019`, videos `2019-07-14T…`: one day each;
# undated files (NULL) come last.
NEWEST_FIRST: Final = f" ORDER BY {DAY}(files.media_date) DESC, files.path"
LIMIT: Final = " LIMIT ?"
WHERE: Final = " WHERE "
AND: Final = " AND "
SOURCE_OF: Final = "SELECT path, size, mtime_ns FROM files WHERE rowid = ?"
VERSIONS: Final = "SELECT files.path, files.size, files.mtime_ns" + _FROM
# Search by meaning (`search.meaning_index`): the rows of the files a search matches,
# those of every file (filters only), one file as a hit, and a probe of one term.
KEYS: Final = "SELECT files.rowid" + _FROM
FILE_KEYS: Final = "SELECT files.rowid FROM files"
HIT_OF: Final = (
    f"SELECT rowid, path, size, mtime_ns, {DAY}(media_date) FROM files"  # noqa: S608
    " WHERE rowid = ?"
)
PROBE: Final = f"SELECT 1 FROM temp.{TABLE} WHERE {TABLE} MATCH ? LIMIT 1"  # noqa: S608
# The folder view (`browse`): every file of the index, then those of one folder (the
# paths between `<folder>/` and `<folder>0`, `0` following `/`: the primary key).
ALL_FILES: Final = "SELECT path, size FROM files"
FOLDER_FILES: Final = (
    f"SELECT rowid, path, size, {DAY}(media_date) FROM files"  # noqa: S608
    " WHERE path > ? AND path < ?"
)


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
