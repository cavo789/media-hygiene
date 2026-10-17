r"""One role per folder: a backup folder is only compared (TODO 0204).

A backup folder is read and compared, never changed and never the reason a copy goes.
Preferred or protected, it would steer the kept copy; excluded, it would not be read:
a folder that is both, or lies inside the other (or holds it), is refused, naming both.
Host paths are compared as the host does: `C:\Photos` ignores case, `/home/me` does not.
"""

from __future__ import annotations

import re
from pathlib import PurePath, PurePosixPath, PureWindowsPath
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Mapping

_DRIVE: Final = re.compile(r"^[A-Za-z]:")


def _host_path(path: str) -> PurePath:
    r"""Read a host path with the rules of its system.

    Args:
        path: A configured folder, `C:\Photos` or `/home/me/Photos`.

    Returns:
        A Windows path when it starts with a drive letter, a POSIX path otherwise.
    """
    return PureWindowsPath(path) if _DRIVE.match(path) else PurePosixPath(path)


def overlap(first: str, second: str) -> bool:
    """Tell whether two host folders are one, or one lies inside the other.

    Args:
        first: A host folder.
        second: Another one.

    Returns:
        True when they are of one system and share their path from the root.
    """
    one, two = _host_path(first), _host_path(second)
    if type(one) is not type(two):
        return False
    return one.is_relative_to(two) or two.is_relative_to(one)


def check_backup_roles(
    backups: tuple[str, ...], others: Mapping[str, tuple[str, ...]]
) -> None:
    """Refuse a backup folder that has, holds or lies in a folder of another role.

    Args:
        backups: The `folders.backups` host paths.
        others: The other roles, by their `[folders]` key, e.g. `protected`.

    Raises:
        ValueError: The first backup folder overlapping another role, naming both.
    """
    for backup in backups:
        for key, folders in others.items():
            other = next((path for path in folders if overlap(backup, path)), None)
            if other is None:
                continue
            message = _(
                "{backup} (folders.backups) and {other} (folders.{key}) are one "
                "folder or one inside the other: a backup folder is only compared, "
                "give it no other role"
            ).format(backup=backup, other=other, key=key)
            raise ValueError(message)
