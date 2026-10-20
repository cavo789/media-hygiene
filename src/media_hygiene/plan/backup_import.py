"""What only a backup holds, minus what the user already dealt with (0245).

A file only in a backup (0204) is proposed for the library only when its content was
never dealt with: not set aside by a choice before (0216: a burst shot, a near copy,
a file chosen, an unwanted photo; quarantined or purged since), not deleted in the
Explorer (0224, confirmed or still waiting for `review --gone`). Each kept apart is
counted, so a deletion by mistake can still be recovered by hand.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from media_hygiene.scan.models import MediaFile


@dataclass(frozen=True, slots=True)
class DealtWith:
    """Paths (container) of a backup's own files whose content was dealt with before.

    `set_aside`: set aside by a choice (0216) or confirmed deleted (0224);
    `deleted`: deleted in the Explorer, the answer still waiting for `review --gone`.
    """

    set_aside: frozenset[Path] = frozenset()
    deleted: frozenset[Path] = frozenset()

    def holds(self, path: Path) -> bool:
        """Tell whether a file's content was dealt with.

        Args:
            path: A file of the backup.

        Returns:
            True when it is not to propose.
        """
        return path in self.set_aside or path in self.deleted


def proposed(only: Iterable[MediaFile], dealt: DealtWith) -> tuple[MediaFile, ...]:
    """The files only in a backup that were never dealt with.

    Args:
        only: The backup's files without an identical copy in the library.
        dealt: What the journals and the index remember.

    Returns:
        Those to propose, in their order.
    """
    return tuple(file for file in only if not dealt.holds(file.path))


def kept_apart(
    only: Iterable[MediaFile], paths: frozenset[Path]
) -> tuple[MediaFile, ...]:
    """The files of `only` among some paths (set aside, deleted).

    Args:
        only: The backup's files without an identical copy in the library.
        paths: The paths of one reason.

    Returns:
        Those files, in their order.
    """
    return tuple(file for file in only if file.path in paths)
