"""A folder the user named after one event of theirs, told by its dates (0403, 0404).

`Saint Nicolas 2009` holds the photos of one evening: the user named that moment, and
a rule or a move about another event of the same days must not take its files. `Prints
jan10` or `Scans sep10` hold the photos of many moments, printed or scanned together: a
batch, whose files may go elsewhere. Decided with the maintainer (2026-10-25): **by the
dates, no word list**. A folder is an event of the user's when its name means something
(not a date, a device, nor a person's folder) and its dated files leave no gap longer
than `merge_gap_hours`: one event, as `classify` groups them.
"""

from __future__ import annotations

from datetime import timedelta
from itertools import pairwise
from typing import TYPE_CHECKING

from media_hygiene.classify.bands import band_folders
from media_hygiene.classify.folders import FolderRules
from media_hygiene.name_patterns import GENERIC_FOLDERS

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from datetime import datetime

    from media_hygiene.config.classify_settings import ClassifySettings


def folder_rules(settings: ClassifySettings, people: Sequence[str]) -> FolderRules:
    """What folder names say, as `classify` reads them.

    Args:
        settings: `[classify]`: generic folders, layouts, person folders.
        people: The names of `[[people.person]]`.

    Returns:
        The rules.
    """
    generic = (*GENERIC_FOLDERS, *settings.generic_folders)
    rules = FolderRules.build(generic, band_folders(settings))
    return rules.with_people((*people, *settings.person_folders))


def one_moment(dates: Iterable[datetime], gap_hours: float) -> bool:
    """Tell whether dates make one event: no gap longer than `gap_hours` between them.

    Args:
        dates: The dates of a folder's files.
        gap_hours: `[classify] merge_gap_hours`.

    Returns:
        True for one moment; False for no date at all.
    """
    ordered = sorted(dates)
    gap = timedelta(hours=gap_hours)
    return bool(ordered) and all(
        later - first <= gap for first, later in pairwise(ordered)
    )


def named_event(
    label: str | None, rules: FolderRules, dated: tuple[Sequence[datetime], float]
) -> bool:
    """Tell a folder the user named after one event of theirs.

    Args:
        label: The meaning of the folder's name (`FolderRules.label`); None: generic.
        rules: Tells a person's folder.
        dated: The dates of its files, and `merge_gap_hours`.

    Returns:
        True for a named folder of one moment, not a person's.
    """
    if label is None or rules.of_person((label,)):
        return False
    dates, gap_hours = dated
    return one_moment(dates, gap_hours)
