"""`shrink-decisions.json`: the videos chosen on the page of `shrink --try` (0307).

Written in the drafts folder at each choice, read back from the disk to show it, and
read again by the command when the page asks to lighten them. A video is known by its
container path, size and modification time, and its draft by its number: moved,
renamed or changed since the page (Explorer, `sort`, `undo`), it no longer matches and
is skipped, never encoded from a stale path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, ValidationError

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.shrink.candidates import FileKey

CHOICES_FILE: Final = "shrink-decisions.json"
_VERSION: Final = 1


class TryChoice(BaseModel):
    """One video chosen: the version of the file the draft was made from."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    size: int
    mtime_ns: int
    draft: int  # its number in the try: `<run>/<draft>.mp4`

    @property
    def key(self) -> FileKey:
        """The version of the file.

        Returns:
            Its path, size and modification time.
        """
        return (self.path, self.size, self.mtime_ns)


class TryChoices(BaseModel):
    """The choices of one try."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    version: int = _VERSION
    run: str
    chosen: tuple[TryChoice, ...] = ()


def save_choices(target: Path, choices: TryChoices) -> TryChoices | None:
    """Write the choices in one atomic step, then read them back from the disk.

    Args:
        target: The decisions file.
        choices: What to write.

    Returns:
        What the disk holds now.

    Raises:
        OSError: The file could not be written.
    """
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(choices.model_dump_json(indent=2), encoding="utf-8")
    temporary.replace(target)
    return read_choices(target)


def read_choices(target: Path) -> TryChoices | None:
    """Read the choices from the disk.

    Args:
        target: The decisions file.

    Returns:
        Them; None when the file is missing or not one.
    """
    try:
        return TryChoices.model_validate_json(target.read_bytes())
    except OSError, ValidationError:
        return None
