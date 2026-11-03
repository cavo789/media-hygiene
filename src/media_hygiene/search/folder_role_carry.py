r"""Where a folder with a role went, once renamed in Explorer (0580).

A folder renamed keeps its files, so the index still holds them under the former path
until the next audit: each of them, by its content (the full digest, else the size and
the first bytes), is looked for elsewhere with the same name below the folder. A folder
of the disk that holds every one of them, at the same place below it, is a candidate:
*Carry the role to <it>* is offered beside *Remove*. Two candidates (a copy of the
folder) are both listed, none chosen for the user; a folder deleted has none.

Read from the index only, one scan per missing folder (filtered on the sizes in
SQLite); after an audit the former rows are gone and only *Remove* is left.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import sqlite3

_UNDER: Final = (
    "SELECT path, size, COALESCE(full_digest, partial_digest) FROM files"
    " WHERE path >= ? AND path < ? LIMIT ?"
)
_SAME_SIZE: Final = (
    "SELECT path, size, COALESCE(full_digest, partial_digest) FROM files"
    " WHERE size IN (SELECT value FROM json_each(?))"
)
_MOST: Final = 500  # files of the former folder compared: enough to tell, one scan


def carried_to(connection: sqlite3.Connection, former: Path) -> tuple[Path, ...]:
    """The folders on the disk that now hold every indexed file of a gone folder.

    Args:
        connection: The index.
        former: The folder gone, in the container.

    Returns:
        The candidates, sorted; none for a folder deleted or never audited.
    """
    start = f"{former.as_posix().rstrip('/')}/"
    rows = connection.execute(_UNDER, (start, f"{start[:-1]}0", _MOST)).fetchall()
    if not rows or any(content is None for _path, _size, content in rows):
        return ()  # deleted, never audited, or a file never read: nothing proven
    wanted = {(size, content): path.removeprefix(start) for path, size, content in rows}
    sizes = json.dumps(sorted({size for size, _content in wanted}))
    found: Counter[str] = Counter()
    for path, size, content in connection.execute(_SAME_SIZE, (sizes,)):
        below = wanted.get((size, content))
        if below and not path.startswith(start) and path.endswith(f"/{below}"):
            found[path.removesuffix(f"/{below}")] += 1
    held = (Path(root) for root, count in found.items() if count == len(wanted))
    return tuple(sorted(root for root in held if root.is_dir()))
