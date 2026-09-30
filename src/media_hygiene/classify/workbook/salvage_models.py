"""What was salvaged from a workbook, and the drop-down values it may hold."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from media_hygiene.classify.workbook.sheets import Labels
from media_hygiene.constants import Locale
from media_hygiene.i18n import using

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.classify.carry_models import LostEdit
    from media_hygiene.classify.workbook.edits import Edits


@dataclass(frozen=True, slots=True)
class Notes:
    """The free notes typed on each sheet, by row id, event id and category."""

    files: Mapping[str, str] = field(default_factory=dict)
    events: Mapping[str, str] = field(default_factory=dict)
    categories: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Salvaged:
    """What could be read of a workbook: its plan id, the edits, the notes."""

    plan_id: str  # empty when `_meta` is gone
    edits: Edits
    notes: Notes = Notes()
    invalid: tuple[LostEdit, ...] = ()

    @property
    def empty(self) -> bool:
        """Tell whether nothing was typed.

        Returns:
            True without any edit nor note.
        """
        edits, notes = self.edits, self.notes
        return not any(
            (
                edits.files,
                edits.events,
                edits.categories,
                notes.files,
                notes.events,
                notes.categories,
            )
        )


@dataclass(frozen=True, slots=True)
class Words:
    """The drop-down values, in every language and as `_meta` recorded them."""

    stay: frozenset[str]
    yes: frozenset[str]
    no: frozenset[str]

    @classmethod
    def of(cls, recorded: Labels | None) -> Words:
        """Gather them.

        Args:
            recorded: The labels of the workbook, when `_meta` could be read.

        Returns:
            The values.
        """
        labels = [recorded] if recorded else []
        for locale in Locale:
            with using(locale):
                labels.append(Labels.current())
        return cls(
            frozenset(label.stay for label in labels),
            frozenset(label.yes for label in labels),
            frozenset(label.no for label in labels),
        )
