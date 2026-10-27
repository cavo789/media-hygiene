"""`[scan]` — which files are analysed, and which folders are skipped by name."""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from media_hygiene.config.categories import expanded, requested, valid_categories
from media_hygiene.i18n import _
from media_hygiene.scan.intruders import DEFAULT_COMPANIONS
from media_hygiene.scan.whole_read import MEBIBYTE, WHOLE_READ_MB

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_SEPARATORS: Final = ("/", "\\")


class ScanSettings(BaseModel):
    """`[scan]` — which files are analysed: photos, RAW and videos, or those asked for.

    Only media extensions may be asked for (a subset, e.g. `.jpg` only); other files
    are intruders, listed by the audit. Categories name lists of extensions: `photo`,
    `raw`, `video`, `media` and the user's own.
    `excluded_names` are folder names (globs, case ignored) skipped wherever they are,
    on top of the system ones.
    """

    model_config = _FROZEN

    # Before `extensions`: resolving them needs the user's categories.
    categories: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    extensions: tuple[str, ...] = ()
    excluded_names: tuple[str, ...] = ()
    # A folder listing older than this is read again, even if the folder did not change.
    full_check_days: int = Field(default=7, ge=0)  # 0: every folder, every time
    # A picture up to this size is read once into memory: decoded and hashed from it.
    read_whole_mb: int = Field(default=WHOLE_READ_MB, ge=0)  # 0: read twice, as before
    # Names and extensions that follow photos: never listed as intruder files (0410).
    companions: tuple[str, ...] = DEFAULT_COMPANIONS

    @field_validator("companions")
    @classmethod
    def _valid_companions(cls, companions: tuple[str, ...]) -> tuple[str, ...]:
        """Lowercase and trim the companions, drop empty ones and duplicates.

        Args:
            companions: Names (`Thumbs.db`) and extensions with their dot (`.xmp`).

        Returns:
            Them, lowercase, in the configured order.
        """
        parts = (
            part.strip().casefold() for item in companions for part in item.split(",")
        )
        return tuple(dict.fromkeys(part for part in parts if part))

    @field_validator("categories")
    @classmethod
    def _valid_categories(
        cls, categories: dict[str, tuple[str, ...]]
    ) -> dict[str, tuple[str, ...]]:
        """Validate the user's categories (see `categories.valid_categories`).

        Args:
            categories: Configured categories.

        Returns:
            Lowercase names with their normalised extensions.
        """
        return valid_categories(categories)

    @field_validator("extensions")
    @classmethod
    def _valid_extensions(
        cls, extensions: tuple[str, ...], info: ValidationInfo
    ) -> tuple[str, ...]:
        """Keep category names, normalise `PNG`, `png` or `.png` to `.png`.

        Comma-separated values (`"png,webp"`) are split. Empty means every media
        extension. Sidecars are refused: they follow the photo of the same name.

        Args:
            extensions: Configured categories and extensions.
            info: The fields validated before, the categories among them.

        Returns:
            Category names, and extensions with their dot, without duplicates.
        """
        return requested(extensions, info.data.get("categories", {}))

    @field_validator("excluded_names")
    @classmethod
    def _valid_names(cls, names: tuple[str, ...]) -> tuple[str, ...]:
        """Split comma-separated folder names, drop empty ones, refuse paths.

        Args:
            names: Configured folder names or globs, e.g. `Thumbnails`, `.Trash-*`.

        Returns:
            The names as written, trimmed, without duplicates.

        Raises:
            ValueError: A value holds a slash: it is a path, for `excluded`.
        """
        parts = (part.strip() for name in names for part in name.split(","))
        valid = tuple(dict.fromkeys(part for part in parts if part))
        paths = [name for name in valid if any(sep in name for sep in _SEPARATORS)]
        if paths:
            message = _(
                "{path} is a path, not a folder name: use --exclude "
                "(folders.excluded) for one precise folder"
            ).format(path=paths[0])
            raise ValueError(message)
        return valid

    @property
    def read_whole_bytes(self) -> int:
        """The largest picture read once into memory.

        Returns:
            `read_whole_mb` in bytes.
        """
        return self.read_whole_mb * MEBIBYTE

    @property
    def resolved(self) -> tuple[str, ...]:
        """The extensions asked for, categories replaced by their extensions.

        Returns:
            Extensions with their dot; empty when nothing was asked for.
        """
        return expanded(self.extensions, self.categories)
