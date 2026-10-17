"""`clean --decisions`: the files set aside in `search`, checked before the clean.

Each file is named by its host path and the version the index knew. None may lie in a
protected folder: that refuses the whole file, like a burst shot. A file changed or
gone since it was chosen is not refused here: the clean leaves it and says so.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.constants import MediaKind
from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _, ngettext
from media_hygiene.scan.filters import media_kind
from media_hygiene.scan.models import MediaFile
from media_hygiene.services.policy import keep_policy

if TYPE_CHECKING:
    from media_hygiene.report.chosen_decisions import ChosenFile
    from media_hygiene.services.runtime import Runtime


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
    mapper = runtime.mapper
    files = tuple(
        MediaFile(
            path := mapper.to_container(item.path),
            item.size,
            item.mtime_ns,
            media_kind(path) or MediaKind.OTHER,
        )
        for item in chosen
    )
    policy = keep_policy(runtime.settings, mapper)
    locked = [file for file in files if policy.is_protected(file)]
    if locked:
        message = _("{path} is in a protected folder: it is never moved.")
        raise DecisionsError(message.format(path=mapper.to_host(locked[0].path)))
    if files:
        said = ngettext(
            "Your decisions — {count} file chosen in 'search' is set aside.",
            "Your decisions — {count} files chosen in 'search' are set aside.",
            len(files),
        )
        runtime.output.info(said.format(count=len(files)))
    return files
