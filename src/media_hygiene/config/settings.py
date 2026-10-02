"""The validated, immutable settings of one run."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator

from media_hygiene.config.album_settings import AlbumSettings
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.config.inventory_settings import InventorySettings
from media_hygiene.config.patterns import valid_patterns
from media_hygiene.config.places_settings import PlacesSettings
from media_hygiene.config.scan_settings import ScanSettings
from media_hygiene.config.sort_settings import SortSettings
from media_hygiene.constants import (
    GENERATED_NAMES,
    GENERIC_FOLDERS,
    ColorMode,
    Locale,
    Verbosity,
)

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_FIRST_PRINTABLE = 0x20


class GeneralSettings(BaseModel):
    """`[general]` — interface language, log level and colours."""

    model_config = _FROZEN

    locale: Locale = Locale.EN
    verbosity: Verbosity = Verbosity.INFO
    color: ColorMode = ColorMode.AUTO


class FolderSettings(BaseModel):
    """`[folders]` — host paths that steer which copy is kept, never folder names.

    `protected` folders are never modified and always hold the copy kept (identical
    files elsewhere are deleted); `excluded` folders are not analysed at all.
    """

    model_config = _FROZEN

    preferred: tuple[str, ...] = ()
    protected: tuple[str, ...] = ()
    excluded: tuple[str, ...] = ()

    @field_validator("preferred", "protected", "excluded")
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
                message = (
                    f"{path!r} contains a control character: write Windows paths "
                    "between 'single quotes' in config.toml"
                )
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


class CleanSettings(BaseModel):
    """`[clean]` — behaviour of the `clean` command."""

    model_config = _FROZEN

    confirm: bool = True


class Settings(BaseModel):
    """Every setting of the tool, one section per `config.toml` table."""

    model_config = _FROZEN

    general: GeneralSettings = GeneralSettings()
    folders: FolderSettings = FolderSettings()
    scan: ScanSettings = ScanSettings()
    keep: KeepSettings = KeepSettings()
    clean: CleanSettings = CleanSettings()
    classify: ClassifySettings = ClassifySettings()
    sort: SortSettings = SortSettings()
    inventory: InventorySettings = InventorySettings()
    places: PlacesSettings = PlacesSettings()
    album: AlbumSettings = AlbumSettings()
