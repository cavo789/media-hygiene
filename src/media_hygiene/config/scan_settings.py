"""`[scan]` — which files are analysed, and which folders are skipped by name."""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from media_hygiene.config.categories import expanded, requested, valid_categories
from media_hygiene.constants import MEDIA_EXTENSIONS

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_SEPARATORS: Final = ("/", "\\")


class ScanSettings(BaseModel):
    """`[scan]` — which files are analysed: photos, RAW and videos, or those asked for.

    Any extension may be asked for (`pdf`, `docx`): such files are only compared byte
    for byte, never decoded, and their copies are moved to the quarantine. Categories
    name lists of extensions: `photo`, `raw`, `video`, `media` and the user's own.
    `excluded_names` are folder names (globs, case ignored) skipped wherever they are,
    on top of the system ones.
    """

    model_config = _FROZEN

    # Before `extensions`: resolving them needs the user's categories.
    categories: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    extensions: tuple[str, ...] = ()
    excluded_names: tuple[str, ...] = ()

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
            message = (
                f"{paths[0]} is a path, not a folder name: use --exclude "
                "(folders.excluded) for one precise folder"
            )
            raise ValueError(message)
        return valid

    @property
    def resolved(self) -> tuple[str, ...]:
        """The extensions asked for, categories replaced by their extensions.

        Returns:
            Extensions with their dot; empty when nothing was asked for.
        """
        return expanded(self.extensions, self.categories)

    @property
    def other_files(self) -> tuple[str, ...]:
        """The extensions asked for that are not photos, RAW files or videos.

        Returns:
            Those extensions, in the configured order.
        """
        return tuple(ext for ext in self.resolved if ext not in MEDIA_EXTENSIONS)
