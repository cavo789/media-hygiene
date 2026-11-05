"""*Your folders* in the sidebar of every page in the frame (0579), as on the home page.

The run that serves a page registers, once its runtime is built, how to list them
(`cli/context.build_runtime`): the same source as the home page (`cli/home_folders`),
read at each page served: the mount table already in memory, one listing of each
folder's top (no walk, no hash). Nothing registered (a test, a page rendered alone) or
a folder that cannot be read: no list, never an error.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.home_parts import HomeFolder

    type FolderSource = Callable[[], tuple[HomeFolder, ...]]

# The source of this process: at most one, the last registered.
_SOURCES: Final[list[FolderSource]] = []


@dataclass(frozen=True, slots=True)
class ShellFolders:
    """The list of the sidebar."""

    folders: tuple[HomeFolder, ...]

    @property
    def warn(self) -> bool:
        """Whether a folder is missing, as the home page's apricot dot.

        Returns:
            True when one is not fine.
        """
        return any(not folder.ok for folder in self.folders)


def register_folders(source: FolderSource) -> None:
    """Tell the frame how to list the folders of this run.

    Args:
        source: Lists them, as the home page does.
    """
    _SOURCES[:] = [source]


def forget_folders() -> None:
    """Forget the source: the pages show no list."""
    _SOURCES.clear()


def shell_folders() -> ShellFolders | None:
    """The folders to list, read now.

    Returns:
        Them; None without a source, without any folder, or when they cannot be read.
    """
    if not _SOURCES:
        return None
    try:
        folders = _SOURCES[0]()
    except OSError:
        return None
    return ShellFolders(folders) if folders else None
