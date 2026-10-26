"""*Move to an event…* on the search page (0403): photos picked, moved without a rule.

A selection with exceptions is a move, not a rule: the user picks photos (a period, a
search), types the event's name, and they go to `YYYY/YYYY-MM/<name>` (the month of
the earliest one, 0400), below their sort root. Before the GO the page shows them by
source folder, one tick box each: a folder the user named after **another** event
(`own_events.named_event`: a meaningful name, one moment) is unticked by default; a
generic folder, another family member's, loose files are ticked. The proposed name is
that of the user's named folder holding most of the picked photos: its files go to the
same name under the convention. The move is the journaled sort of a group, read back.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path, PureWindowsPath
from typing import TYPE_CHECKING

from media_hygiene.classify.own_events import folder_rules, named_event
from media_hygiene.i18n import _
from media_hygiene.services.group_sort import sorted_group
from media_hygiene.services.plan_rows_index import (
    PlanRows,
    parent_of,
    plan_rows,
    taken_at,
)
from media_hygiene.services.selection_models import (
    MoveView,
    Picked,
    SourceFolder,
    event_path,
)
from media_hygiene.services.sort_inputs import find_workbook, plan_of

if TYPE_CHECKING:
    from collections.abc import Mapping

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
        rows = self._rows()
        groups: dict[str, list[int]] = defaultdict(list)
        names: dict[str, str] = {}
        for key, path in sorted(chosen.paths.items()):
            folder = parent_of(self.runtime.mapper.to_host(path))
            groups[folder].append(key)
            names[folder] = path.parent.name
        named = self._named(names, rows)
        largest = Counter({f: len(groups[f]) for f in named}).most_common(1)
        proposed = named[largest[0][0]] if largest else ""
        typed = event_path(name or proposed)
        return MoveView(
            proposed=proposed,
            month=self._month(rows, chosen),
            name=typed,
            target=self._target(rows, chosen, typed),
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

    def _named(self, names: Mapping[str, str], rows: PlanRows) -> dict[str, str]:
        """The source folders the user named after one event of theirs.

        Args:
            names: The name of each host folder.
            rows: The plan's rows: the dates of each folder's files.

        Returns:
            Their meaning, by host folder.
        """
        settings = self.runtime.settings
        people = [person.name for person in settings.people.person]
        rules = folder_rules(settings.classify, people)
        gap = settings.classify.merge_gap_hours
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
        folder = self._month(self._rows(), chosen) + "/" + typed
        return sorted_group(
            self.runtime, dict.fromkeys(chosen.paths.values(), folder), typed
        )

    def _target(self, rows: PlanRows, chosen: Picked, name: str) -> str:
        r"""The destination as the user will see it in Explorer.

        Args:
            rows: The plan's rows.
            chosen: The photos picked.
            name: The event's name.

        Returns:
            `2009\2009-11\<name>` below the root of most photos; empty without a name.
        """
        if not name:
            return ""
        roots = Counter(
            row.root
            for path in chosen.paths.values()
            if (row := rows.by_path.get(self.runtime.mapper.to_host(path)))
        ).most_common(1)
        month = self._month(rows, chosen).split("/")
        relative = PureWindowsPath(*month, *name.split("/"))
        return str(PureWindowsPath(roots[0][0]) / relative) if roots else str(relative)

    def _month(self, rows: PlanRows, chosen: Picked) -> str:
        """`YYYY/YYYY-MM` of the earliest photo picked: plan's date, else the index's.

        Args:
            rows: The plan's rows.
            chosen: The photos picked.

        Returns:
            The year and month folders.

        Raises:
            ValueError: None of them has a date.
        """
        dates = [
            when
            for path in chosen.paths.values()
            if (when := taken_at(rows.by_path.get(self.runtime.mapper.to_host(path))))
            or (when := chosen.days.get(path))
        ]
        if not dates:
            raise ValueError(
                _("None of these photos has a date: no month to put them in.")
            )
        first = min(dates)
        return f"{first.year:04d}/{first.year:04d}-{first.month:02d}"

    def _rows(self) -> PlanRows:
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
