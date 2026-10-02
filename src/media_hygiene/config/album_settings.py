"""`[album]` — where `album` gathers its hard links."""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, field_validator

_FIRST_PRINTABLE: Final = 0x20


class AlbumSettings(BaseModel):
    """`[album]` — the host folder holding the albums.

    Empty: `Albums` in the `[classify] target` folder. A hard link is a second name on
    the same disk: the albums must be on the disk of the photos they gather.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    root: str = ""

    @field_validator("root")
    @classmethod
    def _no_control_character(cls, root: str) -> str:
        r"""Reject a path holding control characters (`"D:\backup"` in TOML).

        Args:
            root: The configured folder.

        Returns:
            It, unchanged.

        Raises:
            ValueError: It contains a control character.
        """
        if any(ord(char) < _FIRST_PRINTABLE for char in root):
            message = (
                f"{root!r} contains a control character: write Windows paths "
                "between 'single quotes' in config.toml"
            )
            raise ValueError(message)
        return root
