"""The events of the Events tab the user chose not to sort (0574), by content id.

*Do not sort this event* keeps its files' content ids (SHA-256) in
`/config/events/left.toml` (`files`), so that the choice follows a move or a rename;
*Undo my choice* takes them out. Atomic, read back (`event_files`' writer).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.classify.event_files import FOLDER, read_ids, write_ids

if TYPE_CHECKING:
    from collections.abc import Collection
    from pathlib import Path

LEFT: Final = f"{FOLDER}/left.toml"
_FILES: Final = "files"


def read_left(config_dir: Path) -> frozenset[str]:
    """The content ids of the files of the events the user chose not to sort (0574).

    Args:
        config_dir: The folder of `config.toml`.

    Returns:
        Them; none before the first choice.
    """
    if not (config_dir / LEFT).is_file():
        return frozenset()
    return read_ids(config_dir, LEFT, _FILES)


def set_left(config_dir: Path, ids: Collection[str], *, left: bool) -> frozenset[str]:
    """Say an event's files stay where they are, or take that back (0574).

    Args:
        config_dir: The folder of `config.toml`.
        ids: The content ids of its files.
        left: True: not to sort; False: to decide again.

    Returns:
        Every id kept, read back from the disk.
    """
    held = read_left(config_dir)
    wanted = held | set(ids) if left else held - set(ids)
    if wanted != held:
        write_ids(config_dir, LEFT, (_FILES, wanted))
    return read_left(config_dir)
