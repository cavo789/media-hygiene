"""The folder view of `browse`: the tree of the library, then the files of one folder.

`GET /api/folders` answers the tree (host paths, counts, sizes), `POST /api/folder`
the files of one folder, by name, date or size, all of them or the photos or videos
only (`folder_order`), those set aside marked, with what the folder holds so that a
filter that hides everything is said; `POST /api/heaviest` the heaviest files of the
whole library (`heaviest`). Read from the index alone: a file the last audit
did not see is not listed.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.console.formatting import human_size
from media_hygiene.constants import MediaKind
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response
from media_hygiene.scan.filters import media_kind
from media_hygiene.search import statements as sql
from media_hygiene.search.file_card import file_card
from media_hygiene.search.folder_order import (  # pydantic reads them
    Order,
    Shown,
    is_shown,
    ordered,
)
from media_hygiene.search.folder_tree import PHOTOS, folder_counts
from media_hygiene.search.heaviest import (
    HEAVIEST_PATH,
    HeaviestAsked,
    heaviest,
    listed_total,
    video_facts,
)

if TYPE_CHECKING:
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.search.chosen_api import ChosenDesk
    from media_hygiene.search.fts import SearchIndex

BROWSE_PATH: Final = "/browse"
FOLDER_QUERY: Final = "folder"  # `/search?folder=…`: the page opens on it (0405)
FOLDERS_PATH: Final = "/api/folders"
FOLDER_PATH: Final = "/api/folder"
FOLDER_POSTS: Final = frozenset({FOLDER_PATH, HEAVIEST_PATH})
_MAX_PATH: Final = 4096
_AFTER_SLASH: Final = "0"  # the character after `/`: ends the range of a folder


class FolderAsked(BaseModel):
    """`POST /api/folder`: a folder of the tree (host path), its order and kind."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    folder: str = Field(min_length=1, max_length=_MAX_PATH)
    order: Order = "name"
    kind: Shown = "all"


@dataclass(frozen=True, slots=True)
class FolderDesk:
    """Answers the folder view: the tree, and the files of a folder."""

    index: SearchIndex
    mapper: HostPathMapper
    roots: tuple[Path, ...]  # the mounted folders, in the container
    chosen: ChosenDesk  # to mark the files set aside

    def tree(self) -> Response:
        """`GET /api/folders`: every folder under the mounted ones.

        Returns:
            The folders, sorted by path, each with its parent, counts and size.
        """
        rows = self.index.connection.execute(sql.ALL_FILES)
        counts = folder_counts(rows, self.roots)
        tops = {str(root) for root in self.roots}
        folders = [
            {
                "path": self.mapper.to_host(Path(folder)),
                "parent": None
                if folder in tops
                else self.mapper.to_host(Path(folder).parent),
                "name": self.mapper.to_host(Path(folder))
                if folder in tops
                else Path(folder).name,
                "photos": count.photos,
                "videos": count.videos,
                "files": count.files,
                "size": human_size(count.size),
            }
            for folder, count in sorted(counts.items())
        ]
        return json_response(HTTPStatus.OK, {"folders": folders})

    def answer(self, path: str, body: bytes) -> Response:
        """Answer a `POST` of the folder view.

        Args:
            path: `FOLDER_PATH` or `HEAVIEST_PATH`.
            body: The JSON the page sent.

        Returns:
            The files of a folder, or the heaviest of the library.
        """
        if path == HEAVIEST_PATH:
            return self.heaviest(body)
        return self.listing(body)

    def heaviest(self, body: bytes) -> Response:
        """`POST /api/heaviest`: the heaviest files of every mounted folder.

        Args:
            body: The JSON the page sent.

        Returns:
            The files, each with its folder and, for a video, what it is; the total
            listed; 400 for a body that is not a request of the list.
        """
        try:
            asked = HeaviestAsked.model_validate_json(body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        found = heaviest(self.index.connection, asked, self.roots)
        chosen = self.chosen.paths()
        files = [
            {
                **file_card(row, self.mapper, chosen),
                "where": self.mapper.to_host(Path(row[1]).parent),
                "facts": video_facts(found.metadata.get(row[0], {})),
            }
            for row in found.rows
        ]
        answer = {"files": files, "total": listed_total(found), "more": asked.limit}
        return json_response(HTTPStatus.OK, answer)

    def listing(self, body: bytes) -> Response:
        """`POST /api/folder`: the files lying directly in a folder.

        Args:
            body: The JSON the page sent.

        Returns:
            The files, in the order asked; 400 for a body that is not a folder.
        """
        try:
            asked = FolderAsked.model_validate_json(body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        folder = self.mapper.to_container(asked.folder)
        bounds = (f"{folder}/", f"{folder}{_AFTER_SLASH}")
        rows = [
            row
            for row in self.index.connection.execute(sql.FOLDER_FILES, bounds)
            if Path(row[1]).parent == folder
        ]
        kinds = [media_kind(Path(row[1])) for row in rows]
        shown = [row for row in rows if is_shown(Path(row[1]), asked.kind)]
        chosen = self.chosen.paths()
        files = [
            file_card(row, self.mapper, chosen) for row in ordered(shown, asked.order)
        ]
        held = {
            "photos": sum(kind in PHOTOS for kind in kinds),
            "videos": sum(kind is MediaKind.VIDEO for kind in kinds),
        }
        answer: dict[str, object] = {
            "folder": asked.folder,
            "files": files,
            "holds": held,
        }
        return json_response(HTTPStatus.OK, answer)
