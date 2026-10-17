"""Where the copies `clean` removed lay, and the hint their folders gave (0207, 0208).

When `clean` removes a copy, the folder someone named (`Mariage Julie 2015`) would be
lost with it: the index remembers it, attached to the kept file (`index.former_names`).
`tags` makes search words of it; `classify` reads it after the file's own folders.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class FormerCopy:
    """A copy `clean` removed: where it lay, and the mounted folder it lay in."""

    path: Path  # container path of the removed copy
    root: Path  # its folder words are read below this one, as for any file


@dataclass(frozen=True, slots=True)
class FormerHint:
    """The folders of removed copies a proposal read, and whether they agreed.

    `agreed`: the folders gave one meaning, which the file took; otherwise they gave
    several and none was used.
    """

    folders: tuple[Path, ...]
    agreed: bool = True
