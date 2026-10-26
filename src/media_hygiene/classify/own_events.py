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

from collections import defaultdict
from datetime import timedelta
from itertools import pairwise
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.bands import band_folders
from media_hygiene.classify.dating_models import DateSource
from media_hygiene.classify.folders import FolderRules
from media_hygiene.classify.models import SortReason
from media_hygiene.classify.rules.kinds import DATED
from media_hygiene.name_patterns import GENERIC_FOLDERS

_LEVEL: Final = "/"

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from datetime import datetime
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.classify.rules.building import RuleFacts
    from media_hygiene.classify.rules.matchers import Test
    from media_hygiene.config.classify_rules import ClassifyRule
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


def own_folders(facts: RuleFacts, gap_hours: float) -> dict[Path, str]:
    """The files of the folders the user named after one event, and that name (0404).

    Args:
        facts: The folder signals (`existing-folder`: a meaningful name) and the dates.
        gap_hours: `[classify] merge_gap_hours`.

    Returns:
        The name of its folder, by file.
    """
    by_folder: dict[Path, list[Path]] = defaultdict(list)
    for path, signal in facts.folders.items():
        # One name alone: a stage below a named trip (`Montenegro/Budva`) is the trip's.
        named = signal.reason is SortReason.EXISTING_FOLDER and signal.category
        if named and _LEVEL not in signal.category:
            by_folder[path.parent].append(path)
    moments = {
        folder: paths
        for folder, paths in by_folder.items()
        if one_moment(_dates(paths, facts), gap_hours)
    }
    own: dict[Path, str] = {}
    for folder, paths in moments.items():
        if folder not in _main_folders(moments, facts):
            own.update(dict.fromkeys(paths, facts.folders[paths[0]].category))
    return own


def _dates(paths: Sequence[Path], facts: RuleFacts) -> list[datetime]:
    """The dates the files say (not the disk's).

    Args:
        paths: Files.
        facts: Their dates.

    Returns:
        Them.
    """
    dated = [facts.datings[p] for p in paths if p in facts.datings]
    return [d.when for d in dated if d.source is not DateSource.MTIME]


def _main_folders(
    moments: Mapping[Path, Sequence[Path]], facts: RuleFacts
) -> frozenset[Path]:
    """The named folder holding most of each event's files: the one a rule is for.

    A rule remembered from an event (review-sort, search) is written for its main
    folder, whatever its name (`Mariage Hervé et Magda` for the rule `Mariage d'Hervé
    et Magda`): only the other folders of the moment are spared.

    Args:
        moments: The named folders of one moment, and their files.
        facts: The events.

    Returns:
        The main folder of each event.
    """
    largest: dict[str, tuple[int, str, Path]] = {}
    for folder, paths in moments.items():
        event = facts.event_of.get(paths[0])
        if event is None:
            continue
        rank = (len(paths), str(folder), folder)
        if event.event_id not in largest or rank[:2] > largest[event.event_id][:2]:
            largest[event.event_id] = rank
    return frozenset(rank[2] for rank in largest.values())


def spared(rule: ClassifyRule, test: Test, own: Mapping[Path, str]) -> Test:
    """A date rule's test that leaves the user's folders of another event alone.

    That evening, a `date_range` rule took 13 photos out of the user's own `Saint
    Nicolas 2009` folder (2026-10-25): a date rule takes no file of a folder named
    after one event, unless that name is the rule's own category.

    Args:
        rule: The rule.
        test: Its test.
        own: The files of the user's event folders, and their names.

    Returns:
        The test, narrowed for a date rule; unchanged for any other.
    """
    if rule.match not in DATED or not own:
        return test
    name = rule.category.rsplit(_LEVEL, 1)[-1].casefold()

    def narrowed(file: MediaInput) -> bool:
        """Tell whether the rule takes one file.

        Args:
            file: The file.

        Returns:
            Its test, and never a file of a folder named otherwise.
        """
        folder = own.get(file.path)
        return test(file) and (folder is None or folder.casefold() == name)

    return narrowed
