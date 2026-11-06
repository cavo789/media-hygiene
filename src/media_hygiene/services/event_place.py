"""Where a move to an event goes: the target and the layout chosen on the page (0596).

*Sort here now* and *Move to an event…* read `[classify] target` and `layout` as
`config.toml` holds them now (`📐 Where and how to sort` saves them, the page running).
The folder is the layout's, the event's name in it: a layout that names no event
(*Year / Month only*) gets it as a last folder, since the user typed it. An empty layout
("stay where it is") cannot hold a move: the default one is used. Without a target, the
files stay below their own root.
"""

from __future__ import annotations

import string
from collections import Counter
from dataclasses import dataclass
from pathlib import PureWindowsPath
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.layout import Values, render
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.i18n import _
from media_hygiene.services.classify_scope import mounted_target
from media_hygiene.services.plan_rows_index import planned_date

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from media_hygiene.services.plan_rows_index import PlanRows
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.selection_models import Picked

_NAMING: Final = frozenset({"category", "event"})  # the placeholders holding the name


def event_folder(layout: str, when: datetime, name: str) -> str:
    """The event's folder below its root.

    Args:
        layout: `[classify] layout`.
        when: The earliest photo's date.
        name: The event's name, `/` between its folders.

    Returns:
        The layout filled; the name always in it.
    """
    used = layout if layout.strip() else ClassifySettings().layout
    values = Values(
        when.year,
        when.month,
        when.day,
        category=name,
        event=name,
        event_start=when.date().isoformat(),
    )
    folder = render(used, values) or ""
    fields = {field for _text, field, _spec, _conv in string.Formatter().parse(used)}
    return folder if fields & _NAMING else "/".join(filter(None, (folder, name)))


@dataclass(frozen=True, slots=True)
class EventPlace:
    """The destination of the photos picked, with the settings the disk holds now."""

    runtime: Runtime  # read again: the page saves the target and the layout
    rows: PlanRows
    chosen: Picked

    def earliest(self) -> datetime:
        """The earliest photo's date: the plan's, else the index's.

        Returns:
            It.

        Raises:
            ValueError: None of them has a date.
        """
        mapper = self.runtime.mapper
        dates = [
            when
            for path in self.chosen.paths.values()
            if (when := planned_date(self.rows, mapper.to_host(path)))
            or (when := self.chosen.days.get(path))
        ]
        if not dates:
            raise ValueError(
                _("None of these photos has a date: no month to put them in.")
            )
        return min(dates)

    def month(self) -> str:
        """`YYYY/YYYY-MM` of the earliest photo: its event folders are the ones offered.

        Returns:
            The year and month folders.
        """
        first = self.earliest()
        return f"{first.year:04d}/{first.year:04d}-{first.month:02d}"

    def folder(self, name: str) -> str:
        """The folder below the root.

        Args:
            name: The event's name.

        Returns:
            The layout chosen, filled.
        """
        layout = self.runtime.settings.classify.layout
        return event_folder(layout, self.earliest(), name)

    def root(self) -> Path | None:
        """The target chosen.

        Returns:
            Its container path; None: each file stays below its own root.
        """
        return mounted_target(self.runtime)

    def shown(self, name: str) -> str:
        r"""The destination as the user will see it in Explorer.

        Args:
            name: The event's name.

        Returns:
            `<target>\2009\2009-11\<name>`, else below the root of most photos; empty
            without a name.
        """
        if not name:
            return ""
        relative = PureWindowsPath(*self.folder(name).split("/"))
        mapper = self.runtime.mapper
        target = self.root()
        if target is not None:
            return str(PureWindowsPath(mapper.to_host(target)) / relative)
        roots = Counter(
            row.root
            for path in self.chosen.paths.values()
            if (row := self.rows.by_path.get(mapper.to_host(path)))
        ).most_common(1)
        return str(PureWindowsPath(roots[0][0]) / relative) if roots else str(relative)
