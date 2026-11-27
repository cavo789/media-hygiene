"""Remove the people's files `config.toml` no longer links (0300).

Only files of the people folder are removed: a file linked by hand elsewhere stays,
and each one is copied into `.history/` first (0795).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.config.people_files import FOLDER, linked_path
from media_hygiene.file_history import keep_previous
from media_hygiene.people.person_files import SUFFIX, Links

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path


def remove_unlinked(config_dir: Path, before: Iterable[str], links: Links) -> None:
    """Remove the files `config.toml` linked before and no longer does.

    Only files of the people folder are removed: a file linked by hand elsewhere
    stays. Each one is copied into `.history/` first.

    Args:
        config_dir: The folder of `config.toml`.
        before: The files it linked before the change.
        links: Those it links now.
    """
    kept = {file.casefold() for file in (*links.people, links.ignored) if file}
    folder = linked_path(config_dir, FOLDER)
    for file in before:
        if file.casefold() in kept:
            continue
        try:
            path = linked_path(config_dir, file)
        except ValueError:
            continue  # never ours to remove
        if path.parent == folder and path.suffix == SUFFIX:
            keep_previous(path)  # its faces stay recoverable from `.history/` (0795)
            path.unlink(missing_ok=True)
