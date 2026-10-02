"""Lay the choices of the review page over the workbook's edits: one result, no guess.

The workbook is the one source of truth; the page writes its choices beside it, each
with the workbook's value it saw (`base`). For every event or file the page decided:

- the workbook still says `base`: the page's choice is newer, it wins;
- the workbook says what the page chose: they agree;
- the workbook says something else: it was edited on the same event or file after the
  page saw it. Nobody can tell which one the user meant: it is a conflict, which
  `sort` refuses and the page shows, until it is chosen again in one place.

Category edits of the workbook stay as they are: the page only decides events and
files, which win over a category anyway (file > event > category).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from enum import Enum
from typing import TYPE_CHECKING

from media_hygiene.classify.carry_models import EditSheet
from media_hygiene.classify.page_values import EventValue, FileValue
from media_hygiene.classify.workbook.sheets import Labels
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.classify.page_decisions import PageDecisions
    from media_hygiene.classify.workbook.edits import Edits


@dataclass(frozen=True, slots=True)
class Conflict:
    """An event or a file decided in the page, then edited otherwise in the workbook."""

    sheet: EditSheet
    key: str  # the event id or the row id
    page: str  # the page's choice, as text
    workbook: str  # the workbook's value, as text


@dataclass(frozen=True, slots=True)
class Overlaid:
    """The edits once the page's choices are laid over the workbook's."""

    edits: Edits
    applied: int = 0  # choices of the page that decide
    replaced: int = 0  # of which replace an edit of the workbook
    agreed: int = 0  # choices the workbook holds too
    conflicts: tuple[Conflict, ...] = ()


def value_text(value: EventValue | FileValue) -> str:
    """Show a value as the user typed or chose it.

    Args:
        value: An event's or a file's value.

    Returns:
        `name · category`, a folder, or "(stay where it is)".
    """
    stay = Labels.current().stay if value.stay else ""
    if isinstance(value, FileValue):
        return value.folder or stay
    return " · ".join(filter(None, (value.name, value.category or stay)))


def page_cell() -> str:
    """Where a file choice of the page comes from, in place of a workbook cell.

    Returns:
        The translated name of the page.
    """
    return _("review page")


class Verdict(Enum):
    """How the page's choice and the workbook's value meet."""

    PAGE = "page"  # the workbook still holds what the page saw: the page wins
    AGREED = "agreed"  # both hold the same
    CONFLICT = "conflict"  # the workbook changed since, to something else


def overlay(workbook: Edits, page: PageDecisions) -> Overlaid:
    """Apply the page's choices on top of the workbook's edits.

    Args:
        workbook: What the workbook holds now.
        page: The choices of the page, with what the workbook held then.

    Returns:
        The edits `sort` applies, and what was decided where.
    """
    events, files = dict(workbook.events), dict(workbook.files)
    cells = dict(workbook.file_cells)
    verdicts: Counter[Verdict] = Counter()
    replaced = 0
    conflicts: list[Conflict] = []
    for event in page.events:
        now = EventValue.of(workbook.events.get(event.event))
        outcome = verdict(now, event.value, event.base)
        verdicts[outcome] += 1
        if outcome is Verdict.CONFLICT:
            conflicts.append(
                Conflict(EditSheet.EVENTS, event.event, *_texts(event.value, now))
            )
            continue
        replaced += outcome is Verdict.PAGE and not now.empty
        events[event.event] = event.value.edit()
    for file in page.files:
        held = FileValue.of(workbook.files.get(file.row))
        outcome = verdict(held, file.value, file.base)
        verdicts[outcome] += 1
        if outcome is Verdict.CONFLICT:
            conflicts.append(
                Conflict(EditSheet.FILES, file.row, *_texts(file.value, held))
            )
            continue
        replaced += outcome is Verdict.PAGE and not held.empty
        files[file.row] = file.value.choice()
        if outcome is Verdict.PAGE:
            cells[file.row] = page_cell()
    return Overlaid(
        replace(workbook, events=events, files=files, file_cells=cells),
        applied=verdicts[Verdict.PAGE],
        replaced=replaced,
        agreed=verdicts[Verdict.AGREED],
        conflicts=tuple(conflicts),
    )


def verdict[V: (EventValue, FileValue)](now: V, chosen: V, base: V) -> Verdict:
    """Compare the workbook's value with the page's choice and what the page saw.

    Args:
        now: What the workbook holds now.
        chosen: The page's choice.
        base: What the workbook held when the page chose.

    Returns:
        Who decides.
    """
    if now == chosen:
        return Verdict.AGREED
    return Verdict.PAGE if now == base else Verdict.CONFLICT


def _texts[V: (EventValue, FileValue)](chosen: V, now: V) -> tuple[str, str]:
    """Show both sides of a conflict.

    Args:
        chosen: The page's choice.
        now: What the workbook holds now.

    Returns:
        The page's text, then the workbook's.
    """
    return value_text(chosen), value_text(now)
