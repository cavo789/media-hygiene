"""The search with the words typed by hand (0555): read from `/config` at each change.

The words live in `tags/<word>.toml` (`config.hand_tags`), each photo by `{path, id}`;
the search gives them to the files of those paths, as it gives the people's names:
in memory only, the index file never written.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.search import statements as sql
from media_hygiene.search.hits import given_too
from media_hygiene.search.meaning_index import MeaningIndex
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


class HandIndex(MeaningIndex):
    """The search, with the words typed by hand on the photos."""

    def give_hand(self, words: Mapping[Path, tuple[str, ...]]) -> None:
        """Give the photos these words typed by hand, from now on.

        Args:
            words: The words on each photo.
        """
        source = TagSource.HAND
        self._people = given_too(self._people, source, words)
        self._connection.execute(sql.CLEAR_SOURCE, (source.value,))
        self._connection.executemany(
            sql.PUT_WORD,
            [(str(p), w, source.value) for p, values in words.items() for w in values],
        )
        self._connection.commit()  # no transaction left open: a move writes the index
        self.built = None
