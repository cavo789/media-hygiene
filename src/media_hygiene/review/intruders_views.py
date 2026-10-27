"""What the page of `review --intruders` receives: the intruder files, tallied (0428).

Per extension and per folder (host path): how many files, how many bytes. The files
already set aside as intruders are listed as the decisions file holds them.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from media_hygiene.console.formatting import human_size
from media_hygiene.report.chosen_decisions import ChosenFile
from media_hygiene.scan.intruders import tally

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.scan.intruders import Intruder, Tally

_FROZEN = ConfigDict(frozen=True, extra="forbid")


class IntruderRow(BaseModel):
    """An extension or a folder: the key the page posts back, its files, its weight."""

    model_config = _FROZEN

    key: str  # `.zip`, or a folder as the user knows it (host path)
    count: int
    size: str  # human, e.g. `12 MB`


class IntrudersState(BaseModel):
    """Everything the page needs: `GET /api/state`."""

    model_config = _FROZEN

    decisions_place: str
    total: int
    size: str
    extensions: tuple[IntruderRow, ...]
    folders: tuple[IntruderRow, ...]
    set_aside: tuple[ChosenFile, ...]  # read from the disk


def _rows(counted: Tally, name: Callable[[str], str]) -> tuple[IntruderRow, ...]:
    """The rows of a tally, the heaviest first.

    Args:
        counted: The tally.
        name: Turns a key into what the page shows and posts back.

    Returns:
        The rows.
    """
    return tuple(
        IntruderRow(key=name(key), count=count, size=human_size(size))
        for key, count, size in counted.heaviest(len(counted.size))
    )


def intruders_state(
    intruders: Iterable[Intruder],
    set_aside: tuple[ChosenFile, ...],
    where: tuple[HostPathMapper, str],
) -> IntrudersState:
    """Describe the intruder files for the page.

    Args:
        intruders: The intruder files now, protected and backups left out.
        set_aside: The intruder files the decisions file holds.
        where: The path translator, and the decisions file as the user knows it.

    Returns:
        The state.
    """
    mapper, place = where
    found = tuple(intruders)
    return IntrudersState(
        decisions_place=place,
        total=len(found),
        size=human_size(sum(item.size for item in found)),
        extensions=_rows(tally(found), str),
        folders=_rows(
            tally(found, by_folder=True), lambda key: mapper.to_host(Path(key))
        ),
        set_aside=set_aside,
    )
