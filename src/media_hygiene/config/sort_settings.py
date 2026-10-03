"""`[sort]` — how `sort` applies the edited plan of `classify`."""

from __future__ import annotations

from pathlib import PurePath
from typing import Final

from pydantic import BaseModel, ConfigDict, field_validator

from media_hygiene.constants import MEDIA_EXTENSIONS, SIDECAR_EXTENSIONS

# Files the system leaves in folders: a folder holding nothing else is empty.
JUNK_FILES: Final = ("Thumbs.db", "desktop.ini", ".DS_Store")
# A junk name is an exact file name: no pattern, no folder.
_NOT_IN_A_NAME: Final = frozenset("*?[]/\\")


class SortSettings(BaseModel):
    """`[sort]` — confirmation, and the files that do not keep a folder alive."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    confirm: bool = True
    # A source folder left with only these files is emptied: they go to the
    # quarantine, the folder is removed (both journaled, both undone by `undo`).
    junk_files: tuple[str, ...] = JUNK_FILES

    @field_validator("junk_files")
    @classmethod
    def _never_a_photo(cls, names: tuple[str, ...]) -> tuple[str, ...]:
        """Refuse a junk name that could be a photo, a video or a sidecar.

        Only `clean` removes a photo: a media name here would let `sort` set one
        aside as junk.

        Args:
            names: The configured names.

        Returns:
            Them, unchanged.

        Raises:
            ValueError: A name is a pattern, a path, or a media or sidecar name.
        """
        for name in names:
            if not name.strip() or _NOT_IN_A_NAME & set(name):
                message = (
                    f"junk_files: {name!r} is not a plain file name "
                    "(no wildcard, no folder), such as Thumbs.db"
                )
                raise ValueError(message)
            if is_media_name(name):
                message = (
                    f"junk_files: {name!r} is a photo, video or sidecar name: "
                    "only 'clean' may remove such a file"
                )
                raise ValueError(message)
        return names

    @property
    def junk_names(self) -> frozenset[str]:
        """The junk file names, compared case-insensitively.

        Returns:
            Them, casefolded.
        """
        return frozenset(name.casefold() for name in self.junk_files)


def is_media_name(name: str) -> bool:
    """Tell whether a file name is a photo's, a video's or a sidecar's.

    Args:
        name: A file name.

    Returns:
        True for a known media or sidecar extension, any case.
    """
    suffix = PurePath(name).suffix.casefold()
    return suffix in MEDIA_EXTENSIONS or suffix in SIDECAR_EXTENSIONS
