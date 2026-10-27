"""Decide which files are media and which folders are skipped."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.constants import (
    IMAGE_EXTENSIONS,
    MEDIA_EXTENSIONS,
    RAW_EXTENSIONS,
    VIDEO_EXTENSIONS,
    MediaKind,
)
from media_hygiene.paths.host_paths import is_within
from media_hygiene.scan.intruders import DEFAULT_COMPANIONS, is_companion
from media_hygiene.scan.skipped_dirs import SYSTEM_DIR_NAMES, matches_any

if TYPE_CHECKING:
    from pathlib import Path


def media_kind(path: Path) -> MediaKind | None:
    """Classify a file by its extension, case-insensitively.

    Sidecars (`.xmp`, `.aae`, `.thm`) and every other file return None: never touched.

    Args:
        path: File to classify.

    Returns:
        Its media kind, or None when it is not a media file.
    """
    suffix = path.suffix.casefold()
    if suffix in IMAGE_EXTENSIONS:
        return MediaKind.IMAGE
    if suffix in RAW_EXTENSIONS:
        return MediaKind.RAW
    if suffix in VIDEO_EXTENSIONS:
        return MediaKind.VIDEO
    return None


@dataclass(frozen=True, slots=True)
class ScanFilters:
    """Folders the walk must not enter, and the extensions it keeps (media when empty).

    Folders are skipped by host path (`excluded`) or by name (`excluded_names`, globs
    added to the system folder names), wherever they are.
    """

    excluded: tuple[Path, ...] = ()
    extensions: frozenset[str] = frozenset()
    excluded_names: tuple[str, ...] = ()
    companions: tuple[str, ...] = DEFAULT_COMPANIONS

    def is_intruder(self, path: Path) -> bool:
        """Tell whether a file is neither media (whatever `--ext`) nor a companion.

        Args:
            path: A regular file, not a sidecar of a file beside it.

        Returns:
            True for a zip, a docx, a pdf...
        """
        return media_kind(path) is None and not is_companion(path.name, self.companions)

    def accepts(self, path: Path) -> bool:
        """Tell whether a file has one of the extensions analysed.

        Args:
            path: A file.

        Returns:
            True when its extension is listed, or is a media one without a filter.
        """
        return path.suffix.casefold() in (self.extensions or MEDIA_EXTENSIONS)

    def kind_of(self, path: Path) -> MediaKind | None:
        """Classify a file the walk keeps: its media kind.

        Args:
            path: A file.

        Returns:
            Its kind, or None when its extension is not analysed.
        """
        if not self.accepts(path):
            return None
        return media_kind(path)

    def skips_dir(self, path: Path) -> bool:
        """Tell whether a directory must be skipped.

        Args:
            path: Directory about to be entered.

        Returns:
            True for system folders and folders the user excluded by path or by name.
        """
        name = path.name
        if matches_any(name, (*SYSTEM_DIR_NAMES, *self.excluded_names)):
            return True
        return any(is_within(path, folder) for folder in self.excluded)
