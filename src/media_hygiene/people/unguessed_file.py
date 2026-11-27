"""The faces no name is guessed for, in `people/unguessed.toml` (2026-11-16).

The cross of a wrong guess on /person and in the large view: "this is not Fleur, and
I do not want to name it". The face stays to name, shown as nobody's; naming it
takes it off (`give_name`). One file for every such face, at a fixed place, never
linked from `config.toml`: the cross writes it and the file of the name ruled out,
not every person the tool would have guessed next (5 to 13 files on the
maintainer's PC). Written as the people's files are: one face per line, its photo's
host path and content id, the previous version kept in `.history/`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.config.people_files import FACES, UNGUESSED_PATH, linked_path
from media_hygiene.config.photo_ref import write_refs
from media_hygiene.file_history import keep_previous
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from pathlib import Path


def write_unguessed(config_dir: Path, lines: list[str]) -> None:
    """Write the faces no name is guessed for; remove the file when there is none.

    Args:
        config_dir: The folder of `config.toml`.
        lines: The faces, as written (`face_line`).

    Raises:
        OSError: The file cannot be written or removed.
    """
    path = linked_path(config_dir, UNGUESSED_PATH)
    if lines:
        header = _(
            "The faces no name is guessed for (a cross on a wrong guess); naming one "
            "takes it off."
        )
        write_refs(path, header, {FACES: lines})
    elif path.is_file():
        keep_previous(path)
        path.unlink()
