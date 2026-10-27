"""What `mh push` reads of the files: their content for a move, the audit's verdict.

A move on the target is proven by the first and last 64 KiB of both files (128 KiB
read on each side, the target's over the network), each file read once a run. A PC
file the audit found broken, unchanged since (same size and time), never replaces its
copy in the backup.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Final

from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan.hashing import partial_digest

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.plan.push_entries import Stat
    from media_hygiene.services.push_place import Target
    from media_hygiene.services.push_sources import Source
    from media_hygiene.services.runtime import Runtime

_BROKEN: Final = (
    "SELECT path, size, mtime_ns FROM files WHERE broken_reason IS NOT NULL"
)


class ContentCheck:
    """Find a file on the PC by its path in the target; compare two contents."""

    def __init__(self, target: Target, sources: tuple[Source, ...]) -> None:
        """Remember both sides.

        Args:
            target: The target.
            sources: The photo folders taking part.
        """
        self._target = target
        self._sources = sources
        self._digests: dict[Path, str | None] = {}

    def pc_path(self, relative: str) -> Path:
        """Where a path of the target lies on the PC (container).

        Args:
            relative: A path relative to the target (`C/Photos/a.jpg`).

        Returns:
            Its container path (`/data/c/Photos/a.jpg`); below the target itself
            when no source holds it.
        """
        parts = PurePosixPath(relative).parts
        for source in self._sources:
            head = PurePosixPath(source.prefix).parts
            if [part.casefold() for part in parts[: len(head)]] == [
                part.casefold() for part in head
            ]:
                return source.point.joinpath(*parts[len(head) :])
        return self._target.point / relative

    def same(self, new: str, old: str) -> bool:
        """Tell whether a new PC file holds the content of a target file.

        Args:
            new: The PC file, relative to the target.
            old: The target file, relative to the target.

        Returns:
            True when their partial digests match; False when one cannot be read.
        """
        mine = self._digest(self.pc_path(new))
        theirs = self._digest(self._target.point / old)
        return mine is not None and mine == theirs

    def _digest(self, path: Path) -> str | None:
        """The partial digest of a file, read once.

        Args:
            path: The file.

        Returns:
            It; None when it cannot be read.
        """
        if path not in self._digests:
            try:
                self._digests[path] = partial_digest(path)
            except OSError:
                self._digests[path] = None
        return self._digests[path]


class BrokenFinder:
    """The PC files the audit found broken and that did not change since."""

    def __init__(self, runtime: Runtime, check: ContentCheck) -> None:
        """Remember where the index is and how to find a file.

        Args:
            runtime: Settings, mount points and output.
            check: Finds a file of the target on the PC.
        """
        self._index = runtime.index_file
        self._check = check

    def broken(self, files: Mapping[str, Stat]) -> frozenset[str]:
        """Pick the broken ones among the PC files.

        Args:
            files: The PC files, by path relative to the target.

        Returns:
            The paths relative to the target of those broken.
        """
        if not files or self._index is None or not self._index.is_file():
            return frozenset()
        with FactsRepository.open(self._index) as repository:
            rows = repository.connection.execute(_BROKEN).fetchall()
        known = {Path(path): (int(size), int(mtime)) for path, size, mtime in rows}
        return frozenset(
            relative
            for relative, stat in files.items()
            if known.get(self._check.pc_path(relative)) == (stat.size, stat.mtime_ns)
        )
