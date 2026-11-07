"""The files `classify` works on, read from the index, for the grouping preview (0646).

The same choice as a run (media kinds, not empty, not broken, the filters, the mounted
folders, the sidecar days), without its walk: the preview answers from what the latest
audit saw.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, replace
from functools import cache, cached_property
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.dates import zone_of
from media_hygiene.classify.engine import Scope
from media_hygiene.classify.grouping_preview import previewed
from media_hygiene.classify.grouping_trips import Tried
from media_hygiene.classify.whereabouts import load_towns
from media_hygiene.constants import MediaKind
from media_hygiene.errors import MountError
from media_hygiene.index.former_names import former_of
from media_hygiene.index.listing import indexed_files
from media_hygiene.index.takeout_rows import takeout_of
from media_hygiene.paths.host_paths import is_within
from media_hygiene.services.classify_inputs import (
    input_of,
    root_of,
    with_sidecar_days,
    with_takeout,
)
from media_hygiene.services.classify_scope import mounted_target
from media_hygiene.services.policy import scan_filters

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Callable, Mapping
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.geo.gazetteer import Gazetteer
    from media_hygiene.index.listing import IndexedFile
    from media_hygiene.services.runtime import Runtime

_SORTED_KINDS: Final = frozenset({MediaKind.IMAGE, MediaKind.RAW, MediaKind.VIDEO})


def _chooser(
    runtime: Runtime, roots: tuple[Path, ...]
) -> Callable[[IndexedFile], bool]:
    """How a `classify` run chooses its files, for the rows of the index.

    Args:
        runtime: Settings, mount points.
        roots: The mounted folders.

    Returns:
        True for a readable, non-empty media file, not filtered out, mounted.
    """
    filters = scan_filters(runtime.settings, runtime.mapper)
    data_dir = runtime.locations.data_dir

    @cache
    def skipped(folder: Path) -> bool:
        """Tell whether the walk would not enter a folder (once per folder).

        Args:
            folder: The folder.

        Returns:
            True when it or a folder above it is skipped.
        """
        if folder == data_dir or not is_within(folder, data_dir):
            return False
        return filters.skips_dir(folder) or skipped(folder.parent)

    @cache
    def mounted_folder(folder: Path) -> bool:
        """Tell whether a folder lies in a mounted one (once per folder).

        Args:
            folder: The folder.

        Returns:
            True when it does.
        """
        return any(is_within(folder, root) for root in roots)

    def chosen(file: IndexedFile) -> bool:
        """Tell whether a `classify` run would work on a file.

        Args:
            file: A row of the index.

        Returns:
            True when it would.
        """
        integrity = file.facts.integrity
        return (
            bool(file.size)
            and filters.kind_of(file.path) in _SORTED_KINDS
            and not (integrity is not None and integrity.broken_reason is not None)
            and mounted_folder(file.path.parent)
            and not skipped(file.path.parent)
        )

    return chosen


@dataclass(slots=False)
class GroupingLook:
    """Compares two sets of grouping values on the files of the index."""

    runtime: Runtime
    connection: sqlite3.Connection

    @cached_property
    def _towns(self) -> Gazetteer | None:
        """The towns of the trips: read once, on the first preview."""
        return load_towns(self.runtime.settings.classify)

    def files(self) -> list[MediaInput]:
        """The files a `classify` run works on, as the index knows them.

        Returns:
            One input per file.
        """
        runtime, connection = self.runtime, self.connection
        roots = runtime.mounts.data_roots(runtime.locations.data_dir)
        target: tuple[Path, ...] = ()
        with contextlib.suppress(MountError):  # the preview does not need it mounted
            found = mounted_target(runtime)
            target = (found,) if found else ()
        sorted_file = _chooser(runtime, roots)
        found_files: list[MediaInput] = []
        for file in indexed_files(connection):
            if not sorted_file(file):
                continue
            root = root_of(file.path, (*target, *roots), runtime)
            item = input_of(file, root, file.facts)
            item = replace(item, former=former_of(connection, file.path))
            found_files.append(with_takeout(item, takeout_of(connection, file.path)))
        zone = zone_of(runtime.settings.classify.timezone)
        return with_sidecar_days(found_files, zone)

    def __call__(
        self, now: Mapping[str, object], asked: Mapping[str, object]
    ) -> dict[str, object]:
        """Compare the values kept with the values asked.

        Args:
            now: The three values `config.toml` holds.
            asked: The three values the page is trying.

        Returns:
            `grouping_preview.previewed`.
        """
        settings = self.runtime.settings
        classify = settings.classify
        scope = Scope(
            generic=settings.keep.generic_folders,
            people=tuple(person.name for person in settings.people.person),
            towns=self._towns,
        )
        tried = Tried(
            classify.model_copy(update=dict(now)),
            classify.model_copy(update=dict(asked)),
        )
        return previewed(self.files(), tried, scope)
