"""The folder view of `browse`: the tree of the library, then the files of one folder.

`GET /api/folders` answers the tree (host paths, counts, sizes), `POST /api/folder`
the files of one folder, by name, date or size, all of them or the photos or videos
only (`folder_order`), those set aside marked, with what the folder holds so that a
filter that hides everything is said. Read from the index alone: a file the last audit
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
from media_hygiene.review.videos import video_path
from media_hygiene.scan.filters import media_kind
from media_hygiene.search import statements as sql
from media_hygiene.search.folder_order import (  # pydantic reads them
    Order,
    Shown,
    is_shown,
    ordered,
)
from media_hygiene.search.folder_tree import PHOTOS, folder_counts
from media_hygiene.search.views import (
    JPEG,
    ORIGINAL_PREFIX,
    PREVIEW_PREFIX,
    THUMB_PREFIX,
)

if TYPE_CHECKING:
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.search.chosen_api import ChosenDesk
    from media_hygiene.search.folder_order import FileRow
    from media_hygiene.search.fts import SearchIndex

BROWSE_PATH: Final = "/browse"
FOLDERS_PATH: Final = "/api/folders"
FOLDER_PATH: Final = "/api/folder"
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
        files = [self.file(row, chosen) for row in ordered(shown, asked.order)]
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

    def file(self, row: FileRow, chosen: frozenset[str]) -> dict[str, object]:
        """Write one file of the folder for the page.

        Args:
            row: Its key, path, size and day.
            chosen: The host paths of the files set aside.

        Returns:
            The JSON object: name, day, size, addresses, and whether it is aside.
        """
        key, text, size, day = row
        path = Path(text)
        video = media_kind(path) is MediaKind.VIDEO
        return {
            "key": key,
            "name": path.name,
            "date": day,
            "size": human_size(size),
            "thumb": "" if video else f"{THUMB_PREFIX}{key}{JPEG}",
            "preview": "" if video else f"{PREVIEW_PREFIX}{key}{JPEG}",
            "video": video_path(str(key), path) if video else "",
            "original": f"{ORIGINAL_PREFIX}{key}{path.suffix.lower()}",
            "chosen": self.mapper.to_host(path) in chosen,
        }
