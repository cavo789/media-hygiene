"""The values of one event or one file, as the workbook and the page hold them."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, ConfigDict, model_validator

from media_hygiene.classify.workbook.edits import EventEdit, Stay
from media_hygiene.classify.workbook.validation import folder_problem

if TYPE_CHECKING:
    from media_hygiene.classify.workbook.edits import Choice


class Frozen(BaseModel):
    """A frozen, strict pydantic model."""

    model_config = ConfigDict(frozen=True, extra="forbid")


def _checked(text: str) -> str:
    """Refuse a folder that climbs out of the target, or a name Windows refuses.

    Args:
        text: A name, a category or a folder; empty is accepted.

    Returns:
        It, unchanged.

    Raises:
        ValueError: It cannot be used as a folder.
    """
    problem = folder_problem(text) if text else None
    if problem is not None:
        raise ValueError(problem)
    return text


class EventValue(Frozen):
    """An event's name and category, as the Events sheet holds them; empty: none."""

    name: str = ""
    category: str = ""
    stay: bool = False  # the category is "(stay where it is)"

    @model_validator(mode="after")
    def _usable(self) -> Self:
        """Check the name and the category.

        Returns:
            The value.
        """
        _checked(self.name)
        _checked(self.category)
        return self

    @classmethod
    def of(cls, edit: EventEdit | None) -> EventValue:
        """Write down an edit of the Events sheet.

        Args:
            edit: The edit, or None when the row is not edited.

        Returns:
            The value; empty without an edit.
        """
        if edit is None:
            return cls()
        if edit.category is Stay.STAY:
            return cls(name=edit.name, stay=True)
        return cls(name=edit.name, category=edit.category)

    @property
    def empty(self) -> bool:
        """Tell whether nothing is chosen.

        Returns:
            True without name, category nor "stay".
        """
        return not (self.name or self.category or self.stay)

    def edit(self) -> EventEdit:
        """The same, as the workbook reader gives it.

        Returns:
            The edit.
        """
        return EventEdit(self.name, Stay.STAY if self.stay else self.category)


class FileValue(Frozen):
    """A file's final folder, as the Files sheet holds it; empty: none."""

    folder: str = ""
    stay: bool = False  # "(stay where it is)"

    @model_validator(mode="after")
    def _usable(self) -> Self:
        """Check the folder.

        Returns:
            The value.
        """
        _checked(self.folder)
        return self

    @classmethod
    def of(cls, choice: Choice | None) -> FileValue:
        """Write down an edit of the Files sheet.

        Args:
            choice: The folder, "stay", or None when the row is not edited.

        Returns:
            The value; empty without an edit.
        """
        if choice is None:
            return cls()
        return cls(stay=True) if choice is Stay.STAY else cls(folder=choice)

    @property
    def empty(self) -> bool:
        """Tell whether nothing is chosen.

        Returns:
            True without folder nor "stay".
        """
        return not (self.folder or self.stay)

    def choice(self) -> Choice:
        """The same, as the workbook reader gives it.

        Returns:
            The folder, or "stay".
        """
        return Stay.STAY if self.stay else self.folder
