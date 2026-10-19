"""The folders of the map page: their list, their photos, what the page changes (0231).

Each line (`folder_rows`) says how many photos of a folder have no position; a click
shows them and a pin, at the saved position or the town's centre, to drag. Every answer
reads `config.toml` back from the disk: the page shows what `xmp` will read.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.config.places_settings import FolderPosition
from media_hygiene.i18n import _
from media_hygiene.places.config_folders import (
    ignore_name,
    read_ignored,
    restore_name,
    save_folder,
)
from media_hygiene.places.drawer_rows import drawer_rows
from media_hygiene.places.folder_rows import folder_rows, folders_json
from media_hygiene.places.tree_rows import (
    first_unlocated,
    tree_json,
    tree_rows,
    unlocated_below,
)

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from media_hygiene.places.folder_rows import FolderContext, FolderRow
    from media_hygiene.places.tree_rows import TreeRow
    from media_hygiene.services.xmp_towns import IndexedInputs


class FolderAction(StrEnum):
    """What the page asks of a folder."""

    SAVE = "save"  # its position, the pin where it was dropped
    FORGET = "forget"  # its saved position: back to its town's centre, or none
    IGNORE = "ignore"  # its name is no town: `folder_town_ignore`
    RESTORE = "restore"  # a name ignored is a town again (0235): `folder` is the name


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
        self._tree: tuple[TreeRow, ...] | None = None  # the index's: built once
        self._sources: dict[str, Path] = {}

    def state(self) -> dict[str, object]:
        """The folders, read again from `config.toml`, the most photos first.

        Returns:
            Each folder's line: its town, its position, saved or not, found or not,
            its files without a position and how many of them are videos; the
            folder names that are never towns (`ignored`); every folder of the
            index (`tree`, 0242).
        """
        context = self._context
        self._rows = folder_rows(self._inputs, context)
        if self._tree is None:  # seconds on 100,000 files; the index does not change
            self._tree = tree_rows(self._inputs, context.roots, context.mapper)
        return {
            "ignored": list(read_ignored(context.config_file)),
            "tree": tree_json(self._tree),
            "folders": folders_json(self._rows),
        }

    def act(self, act: FolderAct) -> dict[str, object]:
        """Save, forget, ignore or restore, then read the file back.

        Args:
            act: What the page asks, for a folder it listed.

        Returns:
            The new state.

        Raises:
            ValueError: The folder is not one of the lists, or no longer there.
            OSError: The file cannot be written.
        """
        config_file = self._context.config_file
        if act.action is FolderAction.RESTORE:
            restore_name(config_file, act.folder)
            return self.state()
        self._known(act.folder)
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
        """The first pictures and videos without a position of a listed folder.

        Args:
            rank: Its rank in the last state's `folders`.

        Returns:
            Each file's name, host folder, previews and whether it is still there
            (`drawer_rows`); None for an unknown rank.
        """
        if not 0 <= rank < len(self._rows):
            return None
        return self._drawer(self._rows[rank].photos)

    def tree_photos(self, rank: int) -> list[dict[str, object]] | None:
        """The first pictures and videos without a position below a tree's folder.

        Args:
            rank: Its rank in the last state's `tree`.

        Returns:
            As `photos`; None for an unknown rank.
        """
        tree = self._tree or ()
        if not 0 <= rank < len(tree):
            return None
        folder = self._context.mapper.to_container(tree[rank].folder)
        return self._drawer(unlocated_below(self._inputs, folder))

    def _drawer(self, paths: Iterable[Path]) -> list[dict[str, object]]:
        """List the first of these files for the drawer, grouped by folder.

        Args:
            paths: Files without a position.

        Returns:
            The drawer's rows; their previews recorded to be served.
        """
        shown = first_unlocated(paths, self._files)
        return drawer_rows(shown, self._context.mapper, self._sources)

    def _known(self, folder: str) -> None:
        """Refuse a folder neither listed nor in the index's tree, or gone since.

        Args:
            folder: The host path the page sent.

        Raises:
            ValueError: Unknown to the index, or renamed or moved since the audit.
        """
        if folder in {row.folder for row in self._rows}:
            return
        if folder not in {row.folder for row in self._tree or ()}:
            message = _("{folder} is not one of the folders listed")
            raise ValueError(message.format(folder=folder))
        if not self._context.mapper.to_container(folder).is_dir():
            message = _(
                "{folder} is no longer there: renamed or moved since the audit. "
                "Run 'audit' again, then place it under its new name."
            )
            raise ValueError(message.format(folder=folder))

    def preview_source(self, key: str) -> Path | None:
        """Find the picture a preview key names.

        Args:
            key: The key, from the page.

        Returns:
            The file, or None for a key never listed.
        """
        return self._sources.get(key)
