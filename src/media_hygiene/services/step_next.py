"""The 👉 line of a step run beside the home server, for its end toast (0762).

A step run in the window of `mh` while the home server stays up (0355) prints its
*What next* line there; the pages only saw *Done: <stage>.* Printed, the line is also
written into `.mh-step-next.json` of the reports folder (plain text, no markup), and
`GET /api/step` carries it once the step is done (`next`). The next step handed to `mh`
forgets it first: a line is never shown for a step that did not print it.
"""

from __future__ import annotations

import json
from contextlib import suppress
from typing import TYPE_CHECKING, Final

from rich.text import Text

from media_hygiene.paths.locations import Locations
from media_hygiene.services.step_progress import RUNNING_FILE

if TYPE_CHECKING:
    from pathlib import Path

NEXT_FILE: Final = ".mh-step-next.json"
_KEY: Final = "next"


def note_next(markup: str, folder: Path | None = None) -> None:
    """Write the 👉 line of the step running beside the home server.

    Args:
        markup: The line, as printed (Rich markup).
        folder: The reports folder; the mounted one by default.
    """
    reports = Locations().reports_dir if folder is None else folder
    if not (reports / RUNNING_FILE).exists():
        return  # not a step of the home page: nothing reads it
    target = reports / NEXT_FILE
    beside = target.with_name(target.name + ".tmp")
    plain = Text.from_markup(markup).plain
    with suppress(OSError):  # the toast says less, the step goes on
        beside.write_text(json.dumps({_KEY: plain}, ensure_ascii=False), "utf-8")
        beside.replace(target)


def read_next(folder: Path) -> str | None:
    """Read the 👉 line the last step wrote.

    Args:
        folder: The reports folder.

    Returns:
        The line; None when there is none or it cannot be read.
    """
    try:
        said = json.loads((folder / NEXT_FILE).read_text("utf-8"))
    except OSError, ValueError:
        return None
    line = said.get(_KEY) if isinstance(said, dict) else None
    return line if isinstance(line, str) and line else None


def forget_next(folder: Path) -> None:
    """Drop the last step's 👉 line: the next step is said on its own.

    Args:
        folder: The reports folder.
    """
    with suppress(OSError):
        (folder / NEXT_FILE).unlink(missing_ok=True)
