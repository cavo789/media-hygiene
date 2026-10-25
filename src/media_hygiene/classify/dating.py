"""The date chain of one file: the first reliable source wins, the doubt is recorded."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.clocks import clocks_of, doubt_future, shifted
from media_hygiene.classify.dates import (
    CONFIDENCE,
    DOUBTED,
    clock_not_set,
    exif_date,
    folder_dating,
    name_date,
    takeout_date,
    video_date,
    zone_of,
)
from media_hygiene.classify.models import DateSource, Dating
from media_hygiene.plan.name_rules import compile_patterns

if TYPE_CHECKING:
    import re
    from collections.abc import Sequence
    from datetime import tzinfo
    from pathlib import Path

    from media_hygiene.classify.clocks import Clock
    from media_hygiene.classify.folders import FolderRules
    from media_hygiene.classify.models import MediaInput
    from media_hygiene.config.classify_settings import ClassifySettings

_NS: Final = 1_000_000_000


def _today() -> date:
    """The day of the run, local.

    Returns:
        It.
    """
    return datetime.now().astimezone().date()


@dataclass(frozen=True, slots=True)
class DatingContext:
    """What the chain needs: folder rules, name patterns, the zone, the clocks."""

    rules: FolderRules
    names: tuple[re.Pattern[str], ...]
    zone: tzinfo
    unset_clocks: frozenset[str] = frozenset()
    clocks: tuple[Clock, ...] = ()  # `[[classify.clocks]]`
    today: date = field(default_factory=_today)


def dating_of(file: MediaInput, context: DatingContext) -> Dating:
    """Date one file.

    A camera whose clock is not set gives way to its folders; one a
    `[[classify.clocks]]` rule covers is set right. An EXIF, video or Takeout date
    whose year its folder contradicts is kept but doubted, as is a date after the
    day of the run: the file goes to "to check". The date a Google Photos Takeout
    `.json` records comes after the file's own, before its name.

    Args:
        file: The file.
        context: Rules and settings of the chain.

    Returns:
        Its date; from the mtime (confidence 0) when nothing else tells.
    """
    return doubt_future(_chain(file, context), context.today)


def _chain(file: MediaInput, context: DatingContext) -> Dating:
    """The first reliable date of a file, a clock set right.

    Args:
        file: The file.
        context: Rules and settings of the chain.

    Returns:
        Its date.
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
        (
            takeout_date(file.takeout.taken_at if file.takeout else None, context.zone),
            DateSource.TAKEOUT,
        ),
    ):
        if when is None:
            continue
        found = shifted(Dating(when, source, CONFIDENCE[source]), file, context.clocks)
        if folder is not None and folder.when.year != found.when.year:
            return replace(found, confidence=DOUBTED)
        return found
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


def datings_of(
    files: Sequence[MediaInput], settings: ClassifySettings, rules: FolderRules
) -> dict[Path, Dating]:
    """The date of each file, from its EXIF, its name, its folders or the disk.

    Args:
        files: Every file.
        settings: `[classify]`: name patterns, zone, clocks.
        rules: What folder names say.

    Returns:
        Each file's date.
    """
    context = DatingContext(
        rules,
        compile_patterns(settings.name_dates),
        zone_of(settings.timezone),
        clock_not_set(files, rules),
        clocks_of(settings.clocks),
    )
    return {file.path: dating_of(file, context) for file in files}
