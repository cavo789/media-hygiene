"""The folders of the map page: their list, their photos, what the page changes (0231).

Each line (`folder_rows`) says how many photos of a folder have no position; a click
shows them and a pin, at the saved position or the town's centre, to drag. Every answer
reads `config.toml` back from the disk: the page shows what `xmp` will read.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.config.places_settings import FolderPosition
from media_hygiene.constants import MediaKind
from media_hygiene.i18n import _
from media_hygiene.places.board import JPEG
from media_hygiene.places.clusters import MEMBERS_KEPT
from media_hygiene.places.config_folders import ignore_name, save_folder
from media_hygiene.places.folder_rows import folder_rows
from media_hygiene.review.views import PREVIEW_PREFIX, preview_key
from media_hygiene.scan.filters import media_kind
from media_hygiene.scan.models import MediaFile

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.places.folder_rows import FolderContext, FolderRow
    from media_hygiene.services.xmp_towns import IndexedInputs

_SHOWN: Final = frozenset({MediaKind.IMAGE, MediaKind.RAW})  # a video has no preview


class FolderAction(StrEnum):
    """What the page asks of a folder."""

    SAVE = "save"  # its position, the pin where it was dropped
    FORGET = "forget"  # its saved position: back to its town's centre, or none
    IGNORE = "ignore"  # its name is no town: `folder_town_ignore`


class FolderAct(BaseModel):
    """`POST /api/folder`: save a position, forget it, or say a name is no town."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: FolderAction
    folder: str = Field(min_length=1)  # a host path, as listed
    latitude: float = Field(default=0, ge=-90, le=90)
    longitude: float = Field(default=0, ge=-180, le=180)


class FolderDesk:
    """The folders' list, their photos, and what the page changes of them."""

    def __init__(self, inputs: IndexedInputs, context: FolderContext) -> None:
        """Keep the files of the index.

        Args:
            inputs: Every file and the positions.
            context: The file, the paths, the towns.
        """
        self._inputs = inputs
        self._context = context
        self._files = {file.path: file for file in inputs.files}
        self._rows: tuple[FolderRow, ...] = ()
        self._sources: dict[str, Path] = {}

    def state(self) -> dict[str, object]:
        """The folders, read again from `config.toml`, the most photos first.

        Returns:
            Each folder's line: its town, its position, saved or not, found or not.
        """
        self._rows = folder_rows(self._inputs, self._context)
        return {
            "folders": [
                {
                    "rank": rank,
                    "folder": row.folder,
                    "town": row.town,
                    "country": row.country,
                    "latitude": row.latitude,
                    "longitude": row.longitude,
                    "saved": row.saved,
                    "found": row.found,
                    "count": len(row.photos),
                }
                for rank, row in enumerate(self._rows)
            ]
        }

    def act(self, act: FolderAct) -> dict[str, object]:
        """Save, forget or ignore, then read the file back.

        Args:
            act: What the page asks, for a folder it listed.

        Returns:
            The new state.

        Raises:
            ValueError: The folder is not one of the list.
            OSError: The file cannot be written.
        """
        if act.folder not in {row.folder for row in self._rows}:
            message = _("{folder} is not one of the folders listed")
            raise ValueError(message.format(folder=act.folder))
        config_file = self._context.config_file
        if act.action is FolderAction.SAVE:
            position = FolderPosition(
                folder=act.folder, latitude=act.latitude, longitude=act.longitude
            )
            save_folder(config_file, position)
        elif act.action is FolderAction.FORGET:
            save_folder(config_file, act.folder)
        else:
            name = self._context.mapper.to_container(act.folder).name
            ignore_name(config_file, name)
        return self.state()

    def photos(self, rank: int) -> list[dict[str, object]] | None:
        """The first pictures without a position of a folder.

        Args:
            rank: Its rank in the last state.

        Returns:
            Each picture's name, preview and whether it is still there; None for an
            unknown rank.
        """
        if not 0 <= rank < len(self._rows):
            return None
        shown = [p for p in self._rows[rank].photos if media_kind(p) in _SHOWN]
        found = []
        for path in shown[:MEMBERS_KEPT]:
            file = self._files[path]
            key = preview_key(
                MediaFile(path, file.size, file.mtime_ns, MediaKind.IMAGE)
            )
            self._sources[key] = path
            found.append(
                {
                    "name": path.name,
                    "preview": f"{PREVIEW_PREFIX}{key}{JPEG}",
                    "found": path.is_file(),
                }
            )
        return found

    def preview_source(self, key: str) -> Path | None:
        """Find the picture a preview key names.

        Args:
            key: The key, from the page.

        Returns:
            The file, or None for a key never listed.
        """
        return self._sources.get(key)
