"""`[sort]` — how `sort` applies the edited plan of `classify`."""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict

# Files the system leaves in folders: a folder holding nothing else is empty.
JUNK_FILES: Final = ("Thumbs.db", "desktop.ini", ".DS_Store")


class SortSettings(BaseModel):
    """`[sort]` — confirmation, and the files that do not keep a folder alive."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    confirm: bool = True
    # A source folder left with only these files is emptied: they go to the
    # quarantine, the folder is removed (both journaled, both undone by `undo`).
    junk_files: tuple[str, ...] = JUNK_FILES

    @property
    def junk_names(self) -> frozenset[str]:
        """The junk file names, compared case-insensitively.

        Returns:
            Them, casefolded.
        """
        return frozenset(name.casefold() for name in self.junk_files)
