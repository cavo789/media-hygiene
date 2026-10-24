"""The faces of the people set aside, kept in the cache's index (TODO 0328).

The people page remembers the faces of a group it sets aside, anonymously: no name, no
path, nothing in `/config`. Each change opens the index for that change only, then
reads back what it holds, so the page says what is remembered, not what was meant to
be. Without a persistent cache nothing is remembered: the photos are still set aside.
"""

from __future__ import annotations

import contextlib
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.index.aside_faces import AsideFaces, forget, remember, remembered
from media_hygiene.index.repository import FactsRepository

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

_ID_FORMAT: Final = "%Y%m%d-%H%M%S"
_DATE_FORMAT: Final = "%Y-%m-%d"


def new_aside() -> str:
    """The id of a person set aside now: the local date and time.

    Returns:
        `YYYYMMDD-HHMMSS`.
    """
    return datetime.now(tz=UTC).astimezone().strftime(_ID_FORMAT)


def aside_date(aside: str) -> str:
    """The day a person was set aside, as the page shows it.

    Args:
        aside: Its id.

    Returns:
        `YYYY-MM-DD`; the id itself when it is not a date.
    """
    try:
        moment = datetime.strptime(aside, _ID_FORMAT).replace(tzinfo=UTC)
    except ValueError:
        return aside
    return moment.strftime(_DATE_FORMAT)


@dataclass(frozen=True, slots=True)
class AsideMemory:
    """The index file that keeps the faces of the people set aside."""

    index_file: Path

    @classmethod
    def of(cls, runtime: Runtime) -> AsideMemory | None:
        """The memory of a run: its index, when it persists.

        Args:
            runtime: Mount points.

        Returns:
            It; None without a persistent cache.
        """
        index_file = runtime.index_file
        return None if index_file is None else cls(index_file)

    def remember(self, faces: AsideFaces) -> int:
        """Keep the faces of a person set aside, then count them back.

        Args:
            faces: The person's faces, under a new id or an existing one.

        Returns:
            How many faces the index holds for that person now; 0 when it cannot
            be written.
        """
        try:
            with FactsRepository.open(self.index_file) as index:
                remember(index.connection, faces)
                kept = remembered(index.connection)
        except sqlite3.Error:
            return 0
        return sum(len(one.embeddings) for one in kept if one.aside == faces.aside)

    def forget(self, embeddings: Iterable[bytes]) -> None:
        """Forget the faces of photos taken back.

        Args:
            embeddings: Their vectors.
        """
        with (
            contextlib.suppress(sqlite3.Error),
            FactsRepository.open(self.index_file) as index,
        ):
            forget(index.connection, embeddings)

    def people(self) -> tuple[AsideFaces, ...]:
        """Every person set aside.

        Returns:
            Them, oldest first; none when the index cannot be read.
        """
        try:
            with FactsRepository.open(self.index_file) as index:
                return remembered(index.connection)
        except sqlite3.Error:
            return ()
