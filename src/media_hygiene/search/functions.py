"""The Python functions the search's SQL calls, registered on its connection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.convention import place_of_path
from media_hygiene.search import statements as sql
from media_hygiene.search.days import NAME as DAY
from media_hygiene.search.days import media_day
from media_hygiene.search.folder_order import kind_of_path
from media_hygiene.search.path_match import REGEX, regex_matches

if TYPE_CHECKING:
    import sqlite3


def register(connection: sqlite3.Connection) -> None:
    """Register `fold`, the day, place and kind readers, and the path regex.

    Args:
        connection: The index.
    """
    connection.create_function(sql.FOLD, 1, str.casefold, deterministic=True)
    connection.create_function(DAY, 1, media_day, deterministic=True)
    connection.create_function(sql.PLACE, 1, place_of_path, deterministic=True)
    connection.create_function(sql.KIND, 1, kind_of_path, deterministic=True)
    connection.create_function(REGEX, 2, regex_matches, deterministic=True)
