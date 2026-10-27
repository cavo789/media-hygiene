"""The validated, immutable settings of one run."""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from media_hygiene.config.album_settings import AlbumSettings
from media_hygiene.config.cache_settings import CacheSettings
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.config.clean_settings import CleanSettings
from media_hygiene.config.folder_roles import check_backup_roles
from media_hygiene.config.inventory_settings import InventorySettings
from media_hygiene.config.patterns import valid_patterns
from media_hygiene.config.people_settings import PeopleSettings
from media_hygiene.config.places_settings import PlacesSettings
from media_hygiene.config.push_settings import PushSettings
from media_hygiene.config.review_settings import ReviewSettings
from media_hygiene.config.scan_settings import ScanSettings
from media_hygiene.config.share_settings import ShareSettings
from media_hygiene.config.shrink_settings import ShrinkSettings
from media_hygiene.config.slideshow_settings import SlideshowSettings
from media_hygiene.config.sort_settings import SortSettings
from media_hygiene.config.tags_settings import TagSettings
from media_hygiene.config.zone import check_timezone
from media_hygiene.constants import ColorMode, Locale, Verbosity
from media_hygiene.i18n import _
from media_hygiene.name_patterns import GENERATED_NAMES, GENERIC_FOLDERS

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_FIRST_PRINTABLE = 0x20


class GeneralSettings(BaseModel):
    """`[general]` — language, time zone, log level, colours, the version check."""

    model_config = _FROZEN

    locale: Locale = Locale.EN
    timezone: str = ""
    verbosity: Verbosity = Verbosity.INFO
    color: ColorMode = ColorMode.AUTO
    check_updates: bool = True  # ask Docker Hub for a newer version, once a day (0267)

    @field_validator("timezone")
    @classmethod
    def _known_timezone(cls, name: str) -> str:
        """Reject a zone name that does not exist, e.g. a typo.

        Args:
            name: The configured zone.

        Returns:
            The name, unchanged.
        """
        return check_timezone(name)


class FolderSettings(BaseModel):
    """`[folders]` — host paths that steer which copy is kept, never folder names.

    `protected` folders are never modified and always hold the copy kept (identical
    files elsewhere are deleted); `excluded` folders are not analysed at all; `backups`
    are read and compared, never changed and never the reason a copy goes (0204).
    """

    model_config = _FROZEN

    preferred: tuple[str, ...] = ()
    protected: tuple[str, ...] = ()
    excluded: tuple[str, ...] = ()
    backups: tuple[str, ...] = ()

    @property
    def untouched(self) -> tuple[str, ...]:
        """The folders never modified: the protected ones and the backups.

        Returns:
            Their host paths.
        """
        return (*self.protected, *self.backups)

    @model_validator(mode="after")
    def _one_role(self) -> Self:
        """Refuse a backup folder that is also preferred, protected or excluded.

        Returns:
            The settings, unchanged.
        """
        others = {"preferred": self.preferred, "protected": self.protected}
        check_backup_roles(self.backups, others | {"excluded": self.excluded})
        return self

    @field_validator("preferred", "protected", "excluded", "backups")
    @classmethod
    def _no_control_character(cls, paths: tuple[str, ...]) -> tuple[str, ...]:
        r"""Reject paths holding control characters.

        In TOML, `"D:\backup"` silently turns `\b` into a backspace: the folder would
        never match, and a *protected* folder would protect nothing.

        Args:
            paths: Configured paths.

        Returns:
            The paths, unchanged.

        Raises:
            ValueError: A path contains a control character.
        """
        for path in paths:
            if any(ord(char) < _FIRST_PRINTABLE for char in path):
                message = _(
                    "{path} contains a control character: write Windows paths "
                    "between 'single quotes' in config.toml"
                ).format(path=repr(path))
                raise ValueError(message)
        return paths


class KeepSettings(BaseModel):
    r"""`[keep]` — names that say nothing, so that another copy's name is kept instead.

    Regular expressions matching the whole name, case ignored: file names without
    extension (`IMG_\d+`) and folder names (`DCIM`). An empty list disables the rule.
    """

    model_config = _FROZEN

    generated_names: tuple[str, ...] = GENERATED_NAMES
    generic_folders: tuple[str, ...] = GENERIC_FOLDERS

    @field_validator("generated_names", "generic_folders")
    @classmethod
    def _valid_patterns(cls, patterns: tuple[str, ...]) -> tuple[str, ...]:
        """Reject patterns that are not valid regular expressions.

        Args:
            patterns: Configured patterns.

        Returns:
            The patterns, unchanged.
        """
        return valid_patterns(patterns)


class Settings(BaseModel):
    """Every setting of the tool, one section per `config.toml` table."""

    model_config = _FROZEN

    general: GeneralSettings = GeneralSettings()
    folders: FolderSettings = FolderSettings()
    scan: ScanSettings = ScanSettings()
    keep: KeepSettings = KeepSettings()
    clean: CleanSettings = CleanSettings()
    review: ReviewSettings = ReviewSettings()
    classify: ClassifySettings = ClassifySettings()
    sort: SortSettings = SortSettings()
    inventory: InventorySettings = InventorySettings()
    cache: CacheSettings = CacheSettings()
    places: PlacesSettings = PlacesSettings()
    album: AlbumSettings = AlbumSettings()
    tags: TagSettings = TagSettings()
    people: PeopleSettings = PeopleSettings()
    push: PushSettings = PushSettings()
    slideshow: SlideshowSettings = SlideshowSettings()
    share: ShareSettings = ShareSettings()
    shrink: ShrinkSettings = ShrinkSettings()
