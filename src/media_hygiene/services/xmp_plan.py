"""Which sidecars `xmp` writes, and what into them: decided from the index alone.

A file is left out when it lies in a protected folder (never written), when an
identical copy of it exists (two copies would get diverging sidecars: `clean` first),
when it has no word of the chosen sources, or when the index is stale for it. An
existing sidecar of the file is merged into (`IMG_1.jpg.xmp`, or `IMG_1.xmp` when it
belongs to this file alone); otherwise `IMG_1.jpg.xmp` is created.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.xmp_write import XmpJob
from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.listing import indexed_files
from media_hygiene.index.tag_rows import TagStore
from media_hygiene.paths.host_paths import is_within
from media_hygiene.scan.filters import media_kind
from media_hygiene.scan.sidecars import companions_of
from media_hygiene.tags.models import TagSource
from media_hygiene.tags.xmp_doc import XmpError, parse
from media_hygiene.tags.xmp_merge import XmpValues, merge, new_document
from media_hygiene.tags.xmp_places import NO_PLACES, places_of

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Sequence

    from media_hygiene.index.listing import IndexedFile

_XMP: Final = ".xmp"


@dataclass(frozen=True, slots=True)
class XmpScope:
    """What the plan reads: the folders asked for, the protected ones, the sources."""

    within: tuple[Path, ...]  # container folders; empty: every file
    protected: tuple[Path, ...]
    sources: tuple[TagSource, ...]
    tool: str  # `media-hygiene <version>`, the creator of new sidecars


@dataclass(slots=True)
class XmpPlan:
    """The sidecars to write, and why the other files are left out."""

    jobs: list[XmpJob] = field(default_factory=list[XmpJob])
    unchanged: int = 0  # their sidecar holds our words already
    protected: int = 0
    copies: int = 0  # an identical copy exists
    without_words: int = 0
    refused: list[tuple[Path, str]] = field(default_factory=list[tuple[Path, str]])


def plan_sidecars(connection: sqlite3.Connection, scope: XmpScope) -> XmpPlan:
    """Decide every sidecar to write.

    Args:
        connection: The open index.
        scope: The folders, the protected ones, the sources.

    Returns:
        The plan.
    """
    files = [
        file
        for file in indexed_files(connection)
        if media_kind(file.path) is not None
        and (not scope.within or any(is_within(file.path, f) for f in scope.within))
    ]
    digests = Counter(
        file.facts.full_digest for file in files if file.facts.full_digest
    )
    store, plan = TagStore(connection), XmpPlan()
    folders: dict[Path, list[str]] = {}
    for file in files:
        if any(is_within(file.path, folder) for folder in scope.protected):
            plan.protected += 1
        elif file.facts.full_digest and digests[file.facts.full_digest] > 1:
            plan.copies += 1
        else:
            values = _values(store, file, scope.sources)
            _plan_file(plan, (file, values), (scope, folders))
    return plan


def _values(
    store: TagStore, file: IndexedFile, sources: Sequence[TagSource]
) -> XmpValues:
    """Our words and sentence for one file.

    Args:
        store: The tags of the index.
        file: The file.
        sources: The sources written into `dc:subject`.

    Returns:
        The values; empty when it has none.
    """
    tags = store.of(PhotoVersion(file.path, file.size, file.mtime_ns))
    words = dict.fromkeys(
        tag.value
        for tag in tags
        if tag.source in sources and tag.source is not TagSource.CAPTION
    )
    captions = [tag.value for tag in tags if tag.source is TagSource.CAPTION]
    return XmpValues(
        tuple(words),
        captions[0] if captions else "",
        places_of(tags) if TagSource.PLACE in sources else NO_PLACES,
    )


def _plan_file(
    plan: XmpPlan,
    what: tuple[IndexedFile, XmpValues],
    where: tuple[XmpScope, dict[Path, list[str]]],
) -> None:
    """Plan the sidecar of one file.

    Args:
        plan: The plan, completed.
        what: The file, and its words and sentence.
        where: The scope, and the names of each folder listed so far.
    """
    file, values = what
    scope, folders = where
    if not (values.subjects or values.description) or not file.path.is_file():
        plan.without_words += 1
        return
    sidecar = sidecar_of(file.path, folders)
    if not sidecar.is_file():
        content = new_document(values, scope.tool).to_bytes()
        plan.jobs.append(XmpJob(file.path, sidecar, content, None))
        return
    try:
        previous = sidecar.read_bytes()
        doc = parse(previous)
    except (OSError, XmpError) as exc:
        plan.refused.append((sidecar, str(exc)))
        return
    if not merge(doc, values):
        plan.unchanged += 1
        return
    plan.jobs.append(XmpJob(file.path, sidecar, doc.to_bytes(), previous))


def sidecar_of(photo: Path, folders: dict[Path, list[str]]) -> Path:
    """The sidecar of a photo: the one there, or the name of a new one.

    Args:
        photo: The photo.
        folders: The names of each folder listed so far (filled here).

    Returns:
        `IMG_1.jpg.xmp` (any case) when there; `IMG_1.xmp` when it belongs to this
        photo alone; else the name of a new `IMG_1.jpg.xmp`.
    """
    folder = photo.parent
    if folder not in folders:
        folders[folder] = sorted(entry.name for entry in folder.iterdir())
    names = folders[folder]
    whole = f"{photo.name}{_XMP}".casefold()
    stem = f"{photo.stem}{_XMP}".casefold()
    for name in names:
        if name.casefold() == whole:
            return folder / name
    for name in names:
        if name.casefold() == stem and companions_of(folder / name, names) == {
            photo.name
        }:
            return folder / name
    return folder / f"{photo.name}{_XMP}"
