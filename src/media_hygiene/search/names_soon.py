"""The names of the people on each photo, read in a thread while the page opens (0354).

Reading the faces and naming them took 1.8 s at each start of `search` (11,457 photos
named, measured on Windows): the server waited for it before answering. A thread now
reads them on a connection of its own while the server starts and the browser loads
the page; the first search waits for what is left (`MeaningIndex`).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from typing import TYPE_CHECKING, Final

from media_hygiene.index.read_only import connect_read_only
from media_hygiene.search.people_words import people_words

if TYPE_CHECKING:
    from concurrent.futures import Future
    from pathlib import Path

    from media_hygiene.config.people_settings import PeopleSettings

type Names = dict[Path, tuple[str, ...]]
_THREAD: Final = "people-names"


def names_soon(index_file: Path, settings: PeopleSettings) -> Future[Names]:
    """Start reading the names of the people on each photo.

    Args:
        index_file: The index, opened read-only by the thread itself.
        settings: `[people]`, with the names.

    Returns:
        The names, once read; its `sqlite3.Error` raised by `result()`.
    """
    pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix=_THREAD)
    later = pool.submit(_read, index_file, settings)
    pool.shutdown(wait=False)  # the thread ends with its one task
    return later


def _read(index_file: Path, settings: PeopleSettings) -> Names:
    """Read the names on a connection of the thread's own.

    Args:
        index_file: The index.
        settings: `[people]`, with the names.

    Returns:
        Each photo with someone named on it, and their names.
    """
    with closing(connect_read_only(index_file)) as connection:
        return people_words(connection, settings)
