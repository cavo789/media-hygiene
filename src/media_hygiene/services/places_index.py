"""Where the photos of the index were taken, for the map of `places`."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

from media_hygiene.classify.whereabouts import located_point
from media_hygiene.constants import MediaKind
from media_hygiene.index.listing import indexed_files
from media_hygiene.index.repository import FactsRepository
from media_hygiene.places.clusters import Located
from media_hygiene.scan.filters import media_kind
from media_hygiene.scan.models import MediaFile
from media_hygiene.services.data_checks import unreadable_index

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


def located_files(runtime: Runtime) -> list[Located]:
    """Every photo and video the index knows a position of.

    Args:
        runtime: Mount points.

    Returns:
        Each file, as audited, and its position; none without an index.

    Raises:
        MountError: The index cannot be read.
    """
    index = runtime.index_file
    if index is None or not index.is_file():
        return []
    try:
        with FactsRepository.open(index) as repository:
            return [
                Located(
                    point,
                    MediaFile(
                        file.path,
                        file.size,
                        file.mtime_ns,
                        media_kind(file.path) or MediaKind.OTHER,
                    ),
                )
                for file in indexed_files(repository.connection)
                if (point := located_point(file.facts.metadata)) is not None
            ]
    except sqlite3.Error as exc:
        raise unreadable_index(runtime, index, exc) from exc
