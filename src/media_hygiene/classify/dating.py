"""The date chain of one file: the first reliable source wins, the doubt is recorded."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.dates import (
    CONFIDENCE,
    DOUBTED,
    exif_date,
    folder_dating,
    name_date,
    video_date,
)
from media_hygiene.classify.models import DateSource, Dating

if TYPE_CHECKING:
    import re
    from datetime import tzinfo

    from media_hygiene.classify.folders import FolderRules
    from media_hygiene.classify.models import MediaInput

_NS: Final = 1_000_000_000


@dataclass(frozen=True, slots=True)
class DatingContext:
    """What the chain needs: folder rules, name patterns, the zone, unset clocks."""

    rules: FolderRules
    names: tuple[re.Pattern[str], ...]
    zone: tzinfo
    unset_clocks: frozenset[str] = frozenset()


def dating_of(file: MediaInput, context: DatingContext) -> Dating:
    """Date one file.

    A camera whose clock is not set gives way to its folders. An EXIF or video date
    whose year its folder contradicts is kept but doubted: the file goes to "to check".

    Args:
        file: The file.
        context: Rules and settings of the chain.

    Returns:
        Its date; from the mtime (confidence 0) when nothing else tells.
    """
    folder = folder_dating(file, context.rules)
    if file.camera in context.unset_clocks and folder is not None:
        return folder
    metadata = file.metadata
    for when, source in (
        (exif_date(file.taken_at), DateSource.EXIF),
        (
            video_date(metadata.recorded_at if metadata else None, context.zone),
            DateSource.VIDEO,
        ),
    ):
        if when is not None:
            doubted = folder is not None and folder.when.year != when.year
            return Dating(when, source, DOUBTED if doubted else CONFIDENCE[source])
    named = name_date(file.path.stem, context.names)
    if named is not None:
        return Dating(named, DateSource.NAME, CONFIDENCE[DateSource.NAME])
    if folder is not None:
        return folder
    when = datetime.fromtimestamp(file.mtime_ns / _NS)  # noqa: DTZ006 - naive local
    return Dating(when, DateSource.MTIME, CONFIDENCE[DateSource.MTIME])


def has_camera_trace(file: MediaInput) -> bool:
    """Tell whether a camera took the file: a make, a model or a position.

    Undated files without any are most often pictures received or downloaded.

    Args:
        file: The file.

    Returns:
        True when the file names a device or holds GPS.
    """
    metadata = file.metadata
    if file.camera:
        return True
    return metadata is not None and bool(
        metadata.make or metadata.model or metadata.located
    )
