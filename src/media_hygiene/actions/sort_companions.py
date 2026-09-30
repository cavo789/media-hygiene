"""Which companion decides the folder of its group, and when the edits disagree.

A file edit on any member (the Files sheet) wins for the whole group; otherwise an
event or category edit reaching one of them, the leading one first; otherwise the
leading file's proposal. Two file edits naming different folders are a conflict: `sort`
refuses the workbook rather than pick one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.workbook.edits import Source

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.classify.workbook.edits import Decision

type Member = tuple[Decision, Path]


@dataclass(frozen=True, slots=True)
class GroupChoice:
    """The decision of a group, and what the user should be told about it.

    Attributes:
        decision: The decision all the members follow.
        conflict: The file edits that disagree (`Files!K7 (IMG_1.MOV)`); empty if none.
        follow: The file deciding and the members whose own event or category edit
            gave another folder; None when there is nothing to say.
    """

    decision: Decision
    conflict: tuple[str, ...] = ()
    follow: tuple[str, tuple[str, ...]] | None = None


def choose(members: list[Member]) -> GroupChoice:
    """Pick the decision of a group of companions.

    Args:
        members: The decisions and files of the group, the leading one first.

    Returns:
        The choice; a conflict when two file edits disagree.
    """
    decision, path = min(members, key=lambda member: member[0].source)
    if decision.source is Source.FILE:
        edited = [member for member in members if member[0].source is Source.FILE]
        if len({member[0].folder for member in edited}) > 1:
            cells = tuple(f"{each.cell} ({file.name})" for each, file in edited)
            return GroupChoice(decision, conflict=cells)
        return GroupChoice(decision)
    others = tuple(
        file.name
        for each, file in members
        if each.source is Source.GROUP and each.folder != decision.folder
    )
    if not others:
        return GroupChoice(decision)
    return GroupChoice(decision, follow=(path.name, others))
