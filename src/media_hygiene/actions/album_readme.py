"""The read-me at the root of the albums' folder (0626): what the folder is.

Never in an album: it must not land in a selection sent to a print service. One only,
in the language of the run that wrote it: both names are recognised.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.constants import ALBUM_README_NAMES
from media_hygiene.i18n.templates import translated_environment

if TYPE_CHECKING:
    from pathlib import Path

_TEMPLATE: Final = "album_readme.txt.j2"


def readme_of(root: Path) -> Path | None:
    """The read-me a folder of albums holds, whatever its language.

    Args:
        root: The folder.

    Returns:
        Its path; None without one.
    """
    found = (root / name for name in ALBUM_README_NAMES)
    return next((path for path in found if path.is_file()), None)


def readme_text() -> str:
    """The read-me, in the language of the run.

    Returns:
        Its text.
    """
    environment = translated_environment("media_hygiene.actions", escaped=())
    return environment.get_template(_TEMPLATE).render()


def write_new(path: Path, text: str) -> None:
    """Write a new text file, never over an existing one.

    Args:
        path: The file; it must not exist.
        text: Its content.
    """
    with path.open("x", encoding="utf-8") as stream:
        stream.write(text)
