"""`clean --decisions`: the files set aside in `search`, checked before the clean.

Each file is named by its host path and the version the index knew. None may lie in a
protected folder: that refuses the whole file, like a burst shot. A file changed or
gone since it was chosen is not refused here: the clean leaves it and says so.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from media_hygiene.constants import MediaKind
from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _, ngettext
from media_hygiene.scan.filters import media_kind
from media_hygiene.scan.models import MediaFile
from media_hygiene.services.policy import backup_folders, keep_policy

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.report.chosen_decisions import ChosenFile
    from media_hygiene.services.runtime import Runtime


class NamedFile(Protocol):
    """A file a decisions file names: host path, and the version the index knew."""

    @property
    def path(self) -> str:
        """The host path."""

    @property
    def size(self) -> int:
        """The size, in bytes."""

    @property
    def mtime_ns(self) -> int:
        """The modification time, in nanoseconds."""


def named_files(runtime: Runtime, named: Sequence[NamedFile]) -> tuple[MediaFile, ...]:
    """Translate files named by host path, size and date into files of the container.

    Args:
        runtime: Settings, mount points and output.
        named: The files, as a decisions file names them.

    Returns:
        The files, as the index knew them.

    Raises:
        DecisionsError: One of them lies in a protected or a backup folder.
    """
    mapper = runtime.mapper
    files = tuple(
        MediaFile(
            path := mapper.to_container(item.path),
            item.size,
            item.mtime_ns,
            media_kind(path) or MediaKind.OTHER,
        )
        for item in named
    )
    policy = keep_policy(runtime.settings, mapper)
    locked = [file for file in files if policy.is_protected(file)]
    if locked:
        message = _("{path} is in a protected folder: it is never moved.")
        raise DecisionsError(message.format(path=mapper.to_host(locked[0].path)))
    backed = backup_folders(runtime.settings, mapper).files_in(files)
    if backed:
        message = _("{path} is in a backup folder: it is never moved.")
        raise DecisionsError(message.format(path=mapper.to_host(backed[0].path)))
    return files


def chosen_files(
    runtime: Runtime, chosen: tuple[ChosenFile, ...]
) -> tuple[MediaFile, ...]:
    """Translate the files chosen in `search` into files of the container.

    Args:
        runtime: Settings, mount points and output.
        chosen: The `chosen` key of the decisions file.

    Returns:
        The files, as the index knew them (size, modification time).

    Raises:
        DecisionsError: One of them lies in a protected folder.
    """
    files = named_files(runtime, chosen)
    if files:
        said = ngettext(
            "Your decisions — {count} file chosen in 'search' is set aside.",
            "Your decisions — {count} files chosen in 'search' are set aside.",
            len(files),
        )
        runtime.output.info(said.format(count=len(files)))
    return files
