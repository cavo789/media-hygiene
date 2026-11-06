"""*Move to an event…* on the search page (0403): photos picked, moved without a rule.

A selection with exceptions is a move, not a rule: the user picks photos (a period, a
search), types the event's name, and they go to the layout's folder holding that name
(the month of the earliest one, 0400), below the target chosen or their root
(`event_place`, 0596). Before the GO the page shows them by
source folder, one tick box each: a folder the user named after **another** event
(`own_events.named_event`: a meaningful name, one moment) is unticked by default; a
generic folder, another family member's, loose files are ticked. The proposed name is
that of the user's named folder holding most of the picked photos: its files go to the
same name under the convention. The move is the journaled sort of a group, read back.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from media_hygiene.classify.own_events import folder_rules, named_event
from media_hygiene.i18n import _
from media_hygiene.services.event_place import EventPlace
from media_hygiene.services.group_sort import moved_group
from media_hygiene.services.group_sort_models import GroupMove
from media_hygiene.services.plan_rows_index import PlanRows, parent_of, plan_rows
from media_hygiene.services.selection_models import (
    MoveView,
    Picked,
    SourceFolder,
    event_path,
    sole_label,
)
from media_hygiene.services.sort_inputs import find_workbook, plan_of

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.classify.folders import FolderRules
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class SelectionMover:
    """Shows, then moves, a selection of photos to an event's folder."""

    runtime: Runtime
    # The rows of the plan read, by (workbook, its mtime): one plan at a time.
    read: dict[tuple[Path, int], PlanRows] = field(default_factory=dict)

    def view(self, chosen: Picked, name: str) -> MoveView:
        """Where the picked photos would go, grouped by source folder.

        Args:
            chosen: Container path of each key picked.
            name: The event's name typed; empty: the one proposed.

        Returns:
            The name proposed and kept, the destination, the source folders.

        Raises:
            ValueError: No picked photo has a date: no month to put it in.
        """
        rows = self.rows()
        groups: dict[str, list[int]] = defaultdict(list)
        names: dict[str, str] = {}
        for key, path in sorted(chosen.paths.items()):
            folder = parent_of(self.runtime.mapper.to_host(path))
            groups[folder].append(key)
            names[folder] = path.parent.name
        named = self._named(names, rows, self._rules())
        largest = Counter({f: len(groups[f]) for f in named}).most_common(1)
        proposed = named[largest[0][0]] if largest else sole_label(names, self._rules())
        typed = event_path(name or proposed)
        place = EventPlace(self.runtime.with_overrides({}), rows, chosen)
        return MoveView(
            proposed=proposed,
            month=place.month(),
            name=typed,
            target=place.shown(typed),
            sources=tuple(
                SourceFolder(
                    folder=folder,
                    files=len(keys),
                    keys=tuple(keys),
                    ticked=named.get(folder, typed).casefold() == typed.casefold(),
                    named=named.get(folder, ""),
                )
                for folder, keys in groups.items()
            ),
        )

    def _rules(self) -> FolderRules:
        """What tells a generic folder name and a person's.

        Returns:
            The rules of the settings.
        """
        settings = self.runtime.settings
        return folder_rules(settings.classify, [p.name for p in settings.people.person])

    def _named(
        self, names: Mapping[str, str], rows: PlanRows, rules: FolderRules
    ) -> dict[str, str]:
        """The source folders the user named after one event of theirs.

        Args:
            names: The name of each host folder.
            rows: The plan's rows: the dates of each folder's files.
            rules: Tell a generic name and a person's folder.

        Returns:
            Their meaning, by host folder.
        """
        gap = self.runtime.settings.classify.merge_gap_hours
        named: dict[str, str] = {}
        for folder, name in names.items():
            label = rules.label(name)
            if label and named_event(label, rules, (rows.dates.get(folder, ()), gap)):
                named[folder] = label
        return named

    def move(self, chosen: Picked, name: str) -> dict[str, object]:
        """Move the photos ticked to the event's folder, journaled, read back.

        Args:
            chosen: Container path of each key ticked.
            name: The event's name.

        Returns:
            The run, as the disk holds it.

        Raises:
            ValueError: No name, or no photo with a date.
        """
        typed = event_path(name)
        if not typed:
            raise ValueError(_("Type the event's name first."))
        fresh = self.runtime.with_overrides({})  # the page saves target and layout
        place = EventPlace(fresh, self.rows(), chosen)
        folders = dict.fromkeys(chosen.paths.values(), place.folder(typed))
        return moved_group(fresh, GroupMove(folders, typed, place.root()))

    def rows(self) -> PlanRows:
        """The rows of the latest classify plan, read once per version of its workbook.

        Returns:
            Them.
        """
        workbook = find_workbook(self.runtime, None)
        stamp = (workbook, workbook.stat().st_mtime_ns)
        if stamp not in self.read:
            _plan_file, plan = plan_of(self.runtime, workbook)
            self.read.clear()  # one plan kept: the latest
            self.read[stamp] = plan_rows(plan)
        return self.read[stamp]
