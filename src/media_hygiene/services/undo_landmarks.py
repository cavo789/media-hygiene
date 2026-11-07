"""After an undo of sidecars, the `spots` rows follow what the sidecars say (0650).

A landmark typed in the large view (0649) is cached in `spots` (source `user`); once
`undo` removes or restores its sidecar, the row takes the sidecar's name again, or
loses the user's: its `stamp` emptied, the next audit names it again (town kept
meanwhile).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.kinds import XMP_ACTIONS
from media_hygiene.index.spot_rows import SpotSource
from media_hygiene.index.spot_user import give_landmark
from media_hygiene.services.landmark_sidecars import sidecar_landmark
from media_hygiene.services.xmp_sidecars import sidecar_of

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.actions.journal import JournalEntry

_IN_FOLDER: Final = "SELECT path FROM spots WHERE path LIKE ? ESCAPE '\\'"
_FORGET: Final = (
    "UPDATE spots SET stamp = '', landmark = CASE WHEN source = ? THEN '' ELSE"
    " landmark END, source = CASE WHEN source = ? THEN '' ELSE source END"
    " WHERE path = ?"
)


def _like(folder: Path) -> str:
    """The `LIKE` pattern of the files right in a folder and below."""
    text = str(folder).replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return text.rstrip("/") + "/%"


def refresh_landmarks(
    connection: sqlite3.Connection, undone: Iterable[JournalEntry]
) -> int:
    """Rewrite the rows of the photos whose sidecar an undo changed, and commit.

    Args:
        connection: The index, open for writing.
        undone: The entries the undo reversed.

    Returns:
        How many rows were refreshed.
    """
    sidecars = {Path(e.path) for e in undone if e.action in XMP_ACTIONS}
    folders: dict[Path, list[str]] = {}
    refreshed = 0
    for folder in {sidecar.parent for sidecar in sidecars}:
        try:
            rows = connection.execute(_IN_FOLDER, (_like(folder),)).fetchall()
        except sqlite3.OperationalError:
            return refreshed  # an index older than `spots`
        for (path,) in rows:
            photo = Path(path)
            if photo.parent != folder or sidecar_of(photo, folders) not in sidecars:
                continue
            said = sidecar_landmark(photo)
            if said.name and said.ours:
                give_landmark(connection, path, said.name)
            else:
                user = SpotSource.USER.value
                connection.execute(_FORGET, (user, user, path))
            refreshed += 1
    connection.commit()
    return refreshed
