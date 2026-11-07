"""The landmark a local model picked for a photo, written over GeoNames' guess (0589).

A pick is asked once per position: a row already of source `vision` is not asked
again, a row of source `user` never (a name typed by hand always wins). The pick
replaces the landmark among the row's searched words, so a search finds it at once.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.index.spot_rows import CURRENT, SpotSource

if TYPE_CHECKING:
    import sqlite3

_SEPARATOR: Final = " ; "
_UNPICKED: Final = (
    "SELECT f.path, f.latitude, f.longitude, s.landmark, s.words, f.rowid"  # noqa: S608
    f" FROM files AS f {CURRENT} WHERE s.source NOT IN (?, ?) ORDER BY f.path"
)
_PICK: Final = (
    "UPDATE spots SET landmark = ?, source = ?, words = ?"
    " WHERE path = ? AND source <> ?"
)


@dataclass(frozen=True, slots=True)
class Unpicked:
    """A located photo whose landmark no model has picked yet."""

    path: str
    latitude: float
    longitude: float
    landmark: str
    words: str
    key: int  # its rowid in `files`: the thumbnail's address


def unpicked(connection: sqlite3.Connection) -> list[Unpicked]:
    """The photos with a row of their current position, neither picked nor typed.

    Args:
        connection: The index.

    Returns:
        Them, by path.
    """
    found = connection.execute(
        _UNPICKED, (SpotSource.USER.value, SpotSource.VISION.value)
    ).fetchall()
    return [Unpicked(*row) for row in found]


def save_pick(connection: sqlite3.Connection, photo: Unpicked, landmark: str) -> None:
    """Store the model's pick (empty: none of the landmarks around), and commit.

    Args:
        connection: The index.
        photo: The photo, as read by `unpicked`.
        landmark: The name picked.
    """
    words = [word for word in photo.words.split(_SEPARATOR) if word]
    if photo.landmark and words and words[0] == photo.landmark:
        words = words[1:]
    spoken = _SEPARATOR.join(dict.fromkeys(w for w in (landmark, *words) if w))
    connection.execute(
        _PICK,
        (landmark, SpotSource.VISION.value, spoken, photo.path, SpotSource.USER.value),
    )
    connection.commit()
