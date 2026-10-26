"""The paths a decisions file names, and how they are renamed (0382)."""

from __future__ import annotations

from pathlib import PureWindowsPath
from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

    from media_hygiene.report.decisions import DecisionsFile


class Pathed(Protocol):
    """An entry known by the path of its file (chosen, unwanted, gone)."""

    @property
    def path(self) -> str:
        """The host path."""

    def model_copy(
        self, *, update: Mapping[str, object] | None = None, deep: bool = False
    ) -> Self:
        """A copy with some fields changed.

        Args:
            update: The fields to change.
            deep: Copy the values too.
        """


def renamed[T: Pathed](
    entries: tuple[T, ...], one: Callable[[str], str]
) -> tuple[T, ...]:
    """Entries known by a `path`, each renamed, the first of two at one path kept.

    Args:
        entries: Chosen, unwanted or gone entries.
        one: Renames a path.

    Returns:
        Them, renamed.
    """
    kept: dict[str, T] = {}
    for entry in entries:
        path = one(entry.path)
        kept.setdefault(path, entry.model_copy(update={"path": path}))
    return tuple(kept.values())


def inside(path: str, folder: str) -> bool:
    """Tell whether a host path is a folder or inside it, whatever the case.

    Args:
        path: A host path.
        folder: A host folder.

    Returns:
        True when it is.
    """
    inner, outer = PureWindowsPath(path.casefold()), PureWindowsPath(folder.casefold())
    return inner == outer or outer in inner.parents


def paths_of(decisions: DecisionsFile) -> tuple[str, ...]:
    """Every file path the decisions name.

    Args:
        decisions: The decisions.

    Returns:
        Them, in file order.
    """
    near = (p for g in decisions.near for p in (g.kept, *g.copies, g.keep) if p)
    return (
        *(p for burst in decisions.bursts for p in (*burst.kept, *burst.discarded)),
        *near,
        *(entry.path for entry in decisions.chosen),
        *(entry.path for entry in decisions.unwanted),
        *(entry.path for entry in decisions.gone),
    )
