"""A list of decisions names each file once: which answer would win otherwise?"""

from __future__ import annotations

from typing import Protocol


class Decided(Protocol):
    """A decision about one file, named by its path."""

    @property
    def path(self) -> str:
        """The file, in host path."""
        ...


def each_path_once[T: Decided](entries: tuple[T, ...]) -> tuple[T, ...]:
    """Refuse a file listed twice.

    Args:
        entries: The files decided.

    Returns:
        The files, unchanged.

    Raises:
        ValueError: A path appears twice.
    """
    paths = [entry.path for entry in entries]
    if len(set(paths)) != len(paths):
        twice = sorted({path for path in paths if paths.count(path) > 1})
        message = f"{twice[0]} is decided twice"
        raise ValueError(message)
    return entries
