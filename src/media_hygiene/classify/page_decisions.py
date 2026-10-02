r"""`sort-decisions.json`: the choices of the `review-sort` page, beside `plan.json`.

```json
{"version": 1, "plan_id": "4f0c…",
 "events": [{"event": "a1b2c3d4e5f6", "value": {"name": "Italy 2023"},
             "base": {}}],
 "files": [{"row": "0123456789abcdef", "value": {"folder": "2023/Work"},
            "base": {}, "category": "Work"}]}
```

The workbook stays the editing surface of the whole plan; the page only adds choices on
top of it. Each choice records `base`: what the workbook said for that event or file
when the page showed it. `sort` knows from it whether the workbook was edited on the
same event afterwards (a conflict, never settled silently) — see `page_overlay`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, Literal, Self

from pydantic import ValidationError, model_validator

from media_hygiene.classify.page_values import EventValue, FileValue, Frozen
from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.text_files import decode_user_text

if TYPE_CHECKING:
    from pathlib import Path

PAGE_DECISIONS_FILE_NAME: Final = "sort-decisions.json"


class EventDecision(Frozen):
    """The page's choice for one event, and what the workbook said when it was made."""

    event: str
    value: EventValue
    base: EventValue = EventValue()


class FileDecision(Frozen):
    """The page's choice for one file, and what the workbook said when it was made."""

    row: str
    value: FileValue
    base: FileValue = FileValue()
    category: str = ""  # the category chosen in the page, shown again there


class PageDecisions(Frozen):
    """Every choice of the page for one plan."""

    version: Literal[1] = 1
    plan_id: str
    events: tuple[EventDecision, ...] = ()
    files: tuple[FileDecision, ...] = ()

    @model_validator(mode="after")
    def _chosen_once(self) -> Self:
        """Refuse an empty choice, or an event or a file chosen twice.

        Returns:
            The decisions.

        Raises:
            ValueError: One of them.
        """
        chosen = [item.value.empty for item in self.events]
        chosen += [item.value.empty for item in self.files]
        if any(chosen):
            message = "a decision without any value"
            raise ValueError(message)
        keys = [item.event for item in self.events] + [item.row for item in self.files]
        if len(set(keys)) != len(keys):
            message = "an event or a file is decided twice"
            raise ValueError(message)
        return self


def read_page_decisions(path: Path, plan_id: str) -> PageDecisions:
    """Read the choices of the page for a plan.

    Args:
        path: `sort-decisions.json`, next to `plan.json`.
        plan_id: The plan they must belong to.

    Returns:
        The choices; none when the file does not exist.

    Raises:
        DecisionsError: The file cannot be read, is not valid, or belongs to another
            plan.
    """
    if not path.is_file():
        return PageDecisions(plan_id=plan_id)
    tip = _(
        "Restore it, or delete it to start the review page over: the workbook "
        "alone then decides."
    )
    try:
        decisions = PageDecisions.model_validate_json(
            decode_user_text(path.read_bytes())
        )
    except (OSError, UnicodeDecodeError, ValidationError) as exc:
        message = _("{path} is not a valid decisions file of the review page.")
        raise DecisionsError(message.format(path=path.name), tip) from exc
    if decisions.plan_id != plan_id:
        message = _("{path} belongs to another classify run.")
        raise DecisionsError(message.format(path=path.name), tip)
    return decisions


def write_page_decisions(path: Path, decisions: PageDecisions) -> None:
    """Save the choices at once: a crash never leaves half a file behind.

    Args:
        path: `sort-decisions.json`.
        decisions: What to save.
    """
    draft = path.with_name(f".{path.name}.partial")
    draft.write_text(decisions.model_dump_json(indent=2) + "\n", encoding="utf-8")
    draft.replace(path)
