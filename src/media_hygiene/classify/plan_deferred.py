"""The edits a narrowed run (`--year`, `--path`) kept for later, in its `plan.json`.

A run with `--year 2015` has no row for the files of 2016: their edits can be neither
carried into its workbook nor called lost, since the files are still there. They are
kept here with the rows and events they were typed for, so that the next carry-over
reads them as if they came from the previous workbook.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Self

from pydantic import Field

from media_hygiene.classify.plan_rows import Frozen, PlanEvent, PlanRow
from media_hygiene.classify.workbook.edits import (
    CategoryEdit,
    Edits,
    EventEdit,
    Stay,
)
from media_hygiene.classify.workbook.salvage_models import Notes

if TYPE_CHECKING:
    from media_hygiene.classify.workbook.edits import Choice


class KeptChoice(Frozen):
    """A folder or a category typed, or "(stay where it is)"."""

    text: str = ""
    stay: bool = False

    @classmethod
    def of(cls, choice: Choice) -> Self:
        """Write a choice down.

        Args:
            choice: The text typed, or `Stay.STAY`.

        Returns:
            The same, as JSON allows it.
        """
        return cls(stay=True) if choice is Stay.STAY else cls(text=str(choice))

    @property
    def choice(self) -> Choice:
        """Read the choice back.

        Returns:
            The text typed, or `Stay.STAY`.
        """
        return Stay.STAY if self.stay else self.text


class KeptEvent(Frozen):
    """The name and the category given to an event."""

    name: str = ""
    category: KeptChoice = KeptChoice()


class KeptCategory(Frozen):
    """A category renamed (or left in place), its "to check" files confirmed."""

    rename: KeptChoice = KeptChoice()
    confirm: bool = False


class DeferredEdits(Frozen):
    """Edits and notes kept for a later run, with the rows and events they name."""

    rows: tuple[PlanRow, ...] = ()
    events: tuple[PlanEvent, ...] = ()
    files: Annotated[dict[str, KeptChoice], Field(default_factory=dict)]
    event_edits: Annotated[dict[str, KeptEvent], Field(default_factory=dict)]
    categories: Annotated[dict[str, KeptCategory], Field(default_factory=dict)]
    file_notes: Annotated[dict[str, str], Field(default_factory=dict)]
    event_notes: Annotated[dict[str, str], Field(default_factory=dict)]
    category_notes: Annotated[dict[str, str], Field(default_factory=dict)]

    @classmethod
    def of(
        cls,
        places: tuple[tuple[PlanRow, ...], tuple[PlanEvent, ...]],
        typed: tuple[Edits, Notes],
    ) -> Self:
        """Keep edits and notes for later.

        Args:
            places: The rows and the events they were typed for.
            typed: The edits and the notes.

        Returns:
            What `plan.json` keeps.
        """
        (rows, events), (edits, notes) = places, typed
        return cls(
            rows=rows,
            events=events,
            files={key: KeptChoice.of(value) for key, value in edits.files.items()},
            event_edits={
                key: KeptEvent(name=edit.name, category=KeptChoice.of(edit.category))
                for key, edit in edits.events.items()
            },
            categories={
                key: KeptCategory(
                    rename=KeptChoice.of(edit.rename), confirm=edit.confirm
                )
                for key, edit in edits.categories.items()
            },
            file_notes=dict(notes.files),
            event_notes=dict(notes.events),
            category_notes=dict(notes.categories),
        )

    @property
    def edits(self) -> Edits:
        """The edits, as the workbook gives them.

        Returns:
            Them.
        """
        return Edits(
            files={key: kept.choice for key, kept in self.files.items()},
            events={
                key: EventEdit(name=kept.name, category=kept.category.choice)
                for key, kept in self.event_edits.items()
            },
            categories={
                key: CategoryEdit(rename=kept.rename.choice, confirm=kept.confirm)
                for key, kept in self.categories.items()
            },
        )

    @property
    def notes(self) -> Notes:
        """The notes, as the workbook gives them.

        Returns:
            Them.
        """
        return Notes(self.file_notes, self.event_notes, self.category_notes)

    @property
    def count(self) -> int:
        """Count the edits and notes kept.

        Returns:
            Files, events and categories, edits and notes alike.
        """
        kept = (
            self.files,
            self.event_edits,
            self.categories,
            self.file_notes,
            self.event_notes,
            self.category_notes,
        )
        return sum(len(part) for part in kept)
