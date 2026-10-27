"""What the map page asks of a folder, or of a town's folders at once (0231, 0383)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.config.places_settings import FolderPosition


class FolderAction(StrEnum):
    """What the page asks of a folder."""

    SAVE = "save"  # its position, the pin where it was dropped
    FORGET = "forget"  # its saved position: back to its town's centre, or none
    IGNORE = "ignore"  # its name is no town: `folder_town_ignore`
    RESTORE = "restore"  # a name ignored is a town again (0235): `folder` is the name


class FolderAct(BaseModel):
    """`POST /api/folder`: save a position, forget it, or say a name is no town.

    `together`: the other folders of the same town (0383), saved or forgotten with
    `folder` in one write of `config.toml`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: FolderAction
    folder: str = Field(min_length=1)  # a host path, as listed
    latitude: float = Field(default=0, ge=-90, le=90)
    longitude: float = Field(default=0, ge=-180, le=180)
    together: tuple[str, ...] = ()

    def folders(self) -> tuple[str, ...]:
        """Every folder the act is for, `folder` first, each once.

        Returns:
            The host paths.
        """
        return tuple(dict.fromkeys((self.folder, *self.together)))

    def changes(self) -> tuple[FolderPosition | str, ...]:
        """What `save_folders` writes: a position per folder, or the folders forgotten.

        Returns:
            The positions to save, or the bare folders to forget.
        """
        if self.action is not FolderAction.SAVE:
            return self.folders()
        return tuple(
            FolderPosition(folder=one, latitude=self.latitude, longitude=self.longitude)
            for one in self.folders()
        )
