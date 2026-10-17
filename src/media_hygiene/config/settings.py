"""The validated, immutable settings of one run."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from media_hygiene.actions.parallel import WORKERS
from media_hygiene.config.album_settings import AlbumSettings
from media_hygiene.config.cache_settings import CacheSettings
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.config.inventory_settings import InventorySettings
from media_hygiene.config.patterns import valid_patterns
from media_hygiene.config.people_settings import PeopleSettings
from media_hygiene.config.places_settings import PlacesSettings
from media_hygiene.config.review_settings import ReviewSettings
from media_hygiene.config.scan_settings import ScanSettings
from media_hygiene.config.sort_settings import SortSettings
from media_hygiene.config.tags_settings import TagSettings
from media_hygiene.config.zone import check_timezone
from media_hygiene.constants import ColorMode, Locale, Verbosity
from media_hygiene.i18n import _
from media_hygiene.name_patterns import GENERATED_NAMES, GENERIC_FOLDERS

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_FIRST_PRINTABLE = 0x20
_PURGE_HINT_DAYS = 30  # `status` suggests purging a quarantine older than that
# Left free on the quarantine's drive by `clean`: a full system drive breaks Windows.
_QUARANTINE_HEADROOM_GB = 1.0


class GeneralSettings(BaseModel):
    """`[general]` — language, time zone, log level, colours."""

    model_config = _FROZEN

    locale: Locale = Locale.EN
    timezone: str = ""
    verbosity: Verbosity = Verbosity.INFO
    color: ColorMode = ColorMode.AUTO

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


class CleanSettings(BaseModel):
    """`[clean]` — behaviour of `clean` and `undo`, and the purge reminder.

    `workers` is how many files `clean`, `undo` and `sort` handle at once: four readers
    read a Windows folder ≈ 4 times faster than one (TODO 0149); a slow USB hard disk,
    whose head seeks between the readers, may prefer 1. `quarantine_headroom_gb` is
    what a `clean` copying to another drive leaves free there (0182, 0191).
    """

    model_config = _FROZEN

    confirm: bool = True
    purge_hint_days: int = Field(default=_PURGE_HINT_DAYS, ge=1)
    workers: int = Field(default=WORKERS, ge=1)
    quarantine_headroom_gb: float = Field(default=_QUARANTINE_HEADROOM_GB, ge=0)

    @property
    def quarantine_headroom(self) -> int:
        """The space `clean` keeps free on the quarantine's drive, in bytes (0191).

        Returns:
            `quarantine_headroom_gb` GiB.
        """
        return int(self.quarantine_headroom_gb * 1024**3)


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
