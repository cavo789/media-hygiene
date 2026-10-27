"""What the map of `places` reads of the index: every file, and where it was taken.

The index is read once: the located files make the clusters, every file the list of
the folders named after a town or placed (0231).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.constants import MediaKind
from media_hygiene.index.repository import FactsRepository
from media_hygiene.places.clusters import Located
from media_hygiene.scan.filters import media_kind
from media_hygiene.scan.models import MediaFile
from media_hygiene.services.data_checks import unreadable_index
from media_hygiene.services.xmp_towns import IndexedInputs, indexed_inputs

if TYPE_CHECKING:
    from media_hygiene.places.board import PlacesBoard
    from media_hygiene.places.folders import FolderDesk
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class OpenedMap:
    """The state of the map page: the clusters and places, the folders."""

    board: PlacesBoard
    folders: FolderDesk


def read_index(runtime: Runtime) -> IndexedInputs:
    """Every file the index knows, and the position of the located ones.

    Args:
        runtime: Mount points.

    Returns:
        The files; none without an index.

    Raises:
        MountError: The index cannot be read.
    """
    index = runtime.index_file
    if index is None or not index.is_file():
        return IndexedInputs((), {})
    try:
        with FactsRepository.open(index) as repository:
            return indexed_inputs(runtime, repository.connection)
    except sqlite3.Error as exc:
        raise unreadable_index(runtime, index, exc) from exc


def located_files(inputs: IndexedInputs) -> list[Located]:
    """The photos and videos with a position, a GPS one or their Takeout `.json`'s.

    Args:
        inputs: The files of the index.

    Returns:
        Each file, as audited, and its position.
    """
    return [
        Located(
            inputs.points[file.path],
            MediaFile(
                file.path,
                file.size,
                file.mtime_ns,
                media_kind(file.path) or MediaKind.SIDECAR,
            ),
        )
        for file in inputs.files
        if file.path in inputs.points
    ]
