"""One file as the folder view shows it: a folder's files and the heaviest alike."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_size
from media_hygiene.constants import MediaKind
from media_hygiene.review.videos import video_path
from media_hygiene.scan.filters import media_kind
from media_hygiene.search.views import (
    JPEG,
    ORIGINAL_PREFIX,
    PREVIEW_PREFIX,
    THUMB_PREFIX,
)

if TYPE_CHECKING:
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.search.folder_order import FileRow


def file_card(
    row: FileRow, mapper: HostPathMapper, chosen: frozenset[str]
) -> dict[str, object]:
    """Write one file for the page.

    Args:
        row: Its key, path, size and day.
        mapper: Container to host path translator.
        chosen: The host paths of the files set aside.

    Returns:
        The JSON object: name, day, size, addresses, and whether it is aside.
    """
    key, text, size, day = row
    path = Path(text)
    video = media_kind(path) is MediaKind.VIDEO
    return {
        "key": key,
        "name": path.name,
        "date": day,
        "size": human_size(size),
        "thumb": "" if video else f"{THUMB_PREFIX}{key}{JPEG}",
        "preview": "" if video else f"{PREVIEW_PREFIX}{key}{JPEG}",
        "video": video_path(str(key), path) if video else "",
        "original": f"{ORIGINAL_PREFIX}{key}{path.suffix.lower()}",
        "chosen": mapper.to_host(path) in chosen,
    }
