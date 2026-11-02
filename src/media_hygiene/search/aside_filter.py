"""The files set aside are gone for every action on a picking (0518).

Once set aside (in the decisions file, not yet moved by *Apply now*), a file is
treated as if it no longer existed by the album, the share, the TV and the event
move, whatever gesture picked it (Ctrl+A, Shift, the rectangle, `all`): the server
drops it, read from the decisions file at each request, so a stale page cannot
bypass it. *Set aside* and *Take back* alone still act on such files.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.i18n import ngettext

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper


@dataclass(frozen=True, slots=True)
class Kept:
    """The files an action may touch, and the sentence on those it left out."""

    files: tuple[Path, ...]
    ignored: int = 0

    @property
    def said(self) -> str:
        """`3 files set aside ignored.`, or empty when none was."""
        if not self.ignored:
            return ""
        return ngettext(
            "{count} file set aside ignored.",
            "{count} files set aside ignored.",
            self.ignored,
        ).format(count=self.ignored)


@dataclass(frozen=True, slots=True)
class AsideFilter:
    """Drops the files set aside from what a page picked."""

    aside: Callable[[], frozenset[str]]  # the host paths set aside, read now
    mapper: HostPathMapper

    def keep(self, files: Iterable[Path]) -> Kept:
        """The files picked that are not set aside.

        Args:
            files: The files picked, in the container.

        Returns:
            Those kept, in order, and how many were left out.
        """
        picked = tuple(files)
        aside = self.aside()
        kept = tuple(path for path in picked if self.mapper.to_host(path) not in aside)
        return Kept(kept, len(picked) - len(kept))
