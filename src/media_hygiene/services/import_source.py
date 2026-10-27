"""Where `import` puts the copies of a source: `From <source>` (0378).

Any folder can be a source: a NAS share, a USB disk, an SD card, an old disk. The copies
go to `<first photo folder>/From <source>`: `From NAS` for a network share (the name of
the first imports, kept), `From E` for a folder of drive `E:`. Two sources of the same
name (two shares, two folders of one disk) each keep their folder's name below it.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Final

from media_hygiene.paths.unc import UNC_FOLDER

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

# A network share: the name the first imports used (maintainer, 2026-10-20).
NAS_SOURCE: Final = "NAS"


def source_name(data_dir: Path, folder: Path) -> str:
    """Name a source after where it is.

    Args:
        data_dir: The data mount point (`/data`).
        folder: The source, in the container.

    Returns:
        `NAS` for a network share, the drive's letter for a disk, else the folder's
        own name.
    """
    try:
        parts = folder.relative_to(data_dir).parts
    except ValueError:
        return folder.name
    if not parts:
        return folder.name
    if parts[0] == UNC_FOLDER:
        return NAS_SOURCE
    return parts[0].upper()


def from_folder(name: str) -> str:
    """The folder of the copies of a source.

    Args:
        name: The source's name.

    Returns:
        `From <name>`.
    """
    return f"From {name}"


def destinations(
    library: Path, data_dir: Path, sources: Sequence[Path]
) -> Mapping[Path, Path]:
    """Where the copies of each source go, below the first photo folder.

    Args:
        library: The first photo folder that is not a source.
        data_dir: The data mount point.
        sources: The sources, in the container.

    Returns:
        The folder of each source's copies.
    """
    names = {source: source_name(data_dir, source) for source in sources}
    shared = Counter(names.values())
    return {
        source: library / from_folder(name) / source.name
        if shared[name] > 1
        else library / from_folder(name)
        for source, name in names.items()
    }
