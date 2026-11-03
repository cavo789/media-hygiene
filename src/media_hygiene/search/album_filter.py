"""A search aimed at an album (0501): its files marked, or kept, or left out.

`/albums` opens the search with `?album=<name>` to add photos to it: the page sends
the album named in its field with each search, and **In the album / Not in the
album** narrows the files found to those already in it, or to the others. Only read:
the albums file never changes here.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.errors import MediaHygieneError

if TYPE_CHECKING:
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.search.query import SearchQuery
    from media_hygiene.share.album_store import AlbumStore

_MAX_NAME = 200


class AlbumAimed(BaseModel):
    """The album a search is aimed at, and whether its files are kept or left out."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1, max_length=_MAX_NAME)
    inside: bool | None = None  # True: its files only; False: the others; None: marked


def album_paths(store: AlbumStore, name: str) -> frozenset[str]:
    """The host paths of an album's files, read from the disk.

    Args:
        store: The albums file.
        name: The album, whatever its case.

    Returns:
        Them; none for an unknown album or a file that cannot be read.
    """
    try:
        album = store.on_disk().albums.named(name)
    except MediaHygieneError, OSError:
        return frozenset()
    return frozenset(entry.path for entry in album.entries) if album else frozenset()


def aimed_query(
    query: SearchQuery, aimed: AlbumAimed, inside: tuple[frozenset[str], HostPathMapper]
) -> SearchQuery:
    """Keep a search to an album's files, or to the others, when asked.

    Args:
        query: The search.
        aimed: The album and the filter.
        inside: Its files (host paths) and the mapper to the container.

    Returns:
        The search, narrowed: an album's files kept among those already kept only.
    """
    if aimed.inside is None:
        return query
    paths, mapper = inside
    container = {str(mapper.to_container(path)) for path in paths}
    filters = query.filters
    if not aimed.inside:
        return replace(
            query, filters=replace(filters, without=tuple(sorted(container)))
        )
    kept = container if filters.only is None else container & set(filters.only)
    return replace(query, filters=replace(filters, only=tuple(sorted(kept))))


def marked(view: dict[str, object], paths: frozenset[str]) -> dict[str, object]:
    """Mark the files found already in the album: adding twice is seen on the tile.

    Args:
        view: The files found, as the page reads them (`hits`, each with its `path`).
        paths: The album's files, host paths.

    Returns:
        The same view, each hit with `inAlbum`.
    """
    hits = view.get("hits")
    for hit in hits if isinstance(hits, list) else ():
        hit["inAlbum"] = hit["path"] in paths
    return view
