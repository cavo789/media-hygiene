"""The files `tags` works on: the photos and videos of the index, from the cache alone.

No folder is walked: the files are those the audits listed, with what they learnt
(dates, sizes, GPS). Each one gets its root, the folder an audit walked, so that the
folder names above it (`Users/Me/Pictures`) are not taken for its words.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.index.listing import indexed_files, walked_roots
from media_hygiene.paths.host_paths import is_within
from media_hygiene.scan.filters import media_kind
from media_hygiene.services.classify_inputs import input_of, root_of

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.services.runtime import Runtime


def require_index(runtime: Runtime, refusal: tuple[str, str] | None = None) -> None:
    """Refuse to run without an index: opening a missing one would create it empty.

    Args:
        runtime: Mount points.
        refusal: The message (with `{folder}`) and the tip, both translated; None
            for those of `tags`.

    Raises:
        MountError: The cache is not mounted, or holds no index yet.
    """
    index = runtime.index_file
    if index is not None and index.is_file():
        return
    cache = runtime.mapper.to_host(runtime.locations.cache_dir)
    message, tip = refusal or (
        _("No index in {folder}: nothing to tag yet."),
        _(
            "Run 'audit' first with the same /cache mount: tags reads what the "
            "audits learnt, and keeps the words there."
        ),
    )
    raise MountError(message.format(folder=cache), tip)


def tag_files(
    runtime: Runtime, connection: sqlite3.Connection, within: Sequence[Path]
) -> tuple[MediaInput, ...]:
    """The media files of the index, below the folders asked for.

    Args:
        runtime: Mount points.
        connection: The open index.
        within: Container folders (`--path`); empty: every file of the index.

    Returns:
        The files, in path order.
    """
    roots = tuple(
        sorted(
            (root.path for root in walked_roots(connection)),
            key=lambda path: len(path.parts),
            reverse=True,
        )
    )
    found: list[MediaInput] = []
    for file in indexed_files(connection):
        if media_kind(file.path) is None:
            continue
        if within and not any(is_within(file.path, folder) for folder in within):
            continue
        found.append(input_of(file, root_of(file.path, roots, runtime), file.facts))
    return tuple(found)
