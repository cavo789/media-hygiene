"""Check what the user typed: folder names Windows accepts, known drop-down values.

Nothing typed is trusted: a path that climbs out of the target (`..`), a drive letter
or a character Windows refuses is refused, with the cell that holds it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.layout import safe_name
from media_hygiene.classify.workbook.edits import Stay
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.classify.workbook.edits import Choice
    from media_hygiene.classify.workbook.sheets import Labels


def text_of(value: object) -> str:
    """The text of a cell: `2021`, not `2021.0`, when Excel turned it into a number.

    Args:
        value: The cell's value.

    Returns:
        Its text, stripped; empty for an empty cell.
    """
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def folder_problem(text: str) -> str | None:
    """Tell why a relative folder cannot be used.

    Args:
        text: A relative folder, separated by slashes or backslashes.

    Returns:
        The reason, translated, or None when it can be used.
    """
    segments = text.replace("\\", "/").strip("/").split("/")
    for segment in segments:
        if segment in {"", ".", ".."}:
            return _("'{text}' is not a folder below the target.").format(text=text)
        if safe_name(segment) != segment:
            return _("'{name}' is not a folder name Windows accepts.").format(
                name=segment
            )
    return None


def folder_of(text: str) -> str:
    """A checked relative folder, `/`-separated.

    Args:
        text: What the user typed, checked by `folder_problem`.

    Returns:
        The folder.
    """
    return text.replace("\\", "/").strip("/")


def choice_of(text: str, labels: Labels) -> Choice:
    """A drop-down value: "(stay where it is)", or a folder.

    Args:
        text: What the user typed or chose.
        labels: The workbook's values.

    Returns:
        `Stay.STAY`, or the folder.
    """
    return Stay.STAY if text == labels.stay else folder_of(text)
