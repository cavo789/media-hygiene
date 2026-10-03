"""Turn the facts of a file into a row of the index, and a row back into facts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.constants import BrokenReason
from media_hygiene.index.facts import FileFacts, Integrity
from media_hygiene.index.video_rows import video_print_of, video_print_row
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.scan.models import VisualFacts

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.scan.models import MediaFile

# Positions in `schema.SELECT`.
_SIZE, _MTIME, _PARTIAL, _FULL, _CHECKED, _REASON, _DETAIL, _VISUAL = range(8)
_VISUAL_VALUES: Final = slice(_VISUAL + 1, _VISUAL + 8)
_METADATA_VERSION, _METADATA = 15, 16
_VIDEO_PRINT: Final = slice(17, 19)
_HEX: Final = 16


def is_current(file: MediaFile, row: Sequence[object]) -> bool:
    """Tell whether a row describes this very version of the file.

    Args:
        file: The file, with the size and mtime seen by the scan.
        row: Its row, as `schema.SELECT` reads it.

    Returns:
        True when the size and the modification time are the same.
    """
    return (row[_SIZE], row[_MTIME]) == (file.size, file.mtime_ns)


def facts_of(row: Sequence[object]) -> FileFacts:
    """Rebuild the facts of a row.

    Args:
        row: A row, as `schema.SELECT` reads it.

    Returns:
        The facts. Unreadable metadata (a corrupt row) reads as never read.
    """
    reason, stored = row[_REASON], row[_METADATA]
    metadata = _metadata_of(stored)
    corrupt = isinstance(stored, str) and metadata is None
    print_version, video_print = video_print_of(row[_VIDEO_PRINT])
    return FileFacts(
        partial_digest=_text(row[_PARTIAL]),
        full_digest=_text(row[_FULL]),
        integrity=Integrity(
            BrokenReason(reason) if isinstance(reason, str) else None,
            _text(row[_DETAIL]) or "",
        )
        if row[_CHECKED]
        else None,
        visual_checked=bool(row[_VISUAL]),
        visual=_visual_of(row[_VISUAL_VALUES]),
        metadata_version=0 if corrupt else _version(row[_METADATA_VERSION]),
        metadata=metadata,
        video_print_version=print_version,
        video_print=video_print,
    )


def row_of(file: MediaFile, facts: FileFacts) -> tuple[object, ...]:
    """Flatten the facts of a file into a row, as `schema.UPSERT` writes it.

    Args:
        file: The file they describe.
        facts: The facts.

    Returns:
        The row.
    """
    reason = facts.broken_reason.value if facts.broken_reason is not None else None
    visual, metadata = facts.visual, facts.metadata
    taken = visual.taken_at if visual is not None else None
    return (
        str(file.path),
        file.size,
        file.mtime_ns,
        facts.partial_digest,
        facts.full_digest,
        int(facts.integrity_checked),
        reason,
        facts.broken_detail,
        int(facts.visual_checked),
        *_visual_row(visual),
        facts.metadata_version,
        metadata.model_dump_json(exclude_none=True) if metadata else None,
        metadata.latitude if metadata else None,
        metadata.longitude if metadata else None,
        taken or (metadata.recorded_at if metadata else None),
        *video_print_row(facts.video_print_version, facts.video_print),
    )


def _visual_row(visual: VisualFacts | None) -> tuple[object, ...]:
    """Flatten visual facts into the version 2 columns.

    Args:
        visual: The facts, or None.

    Returns:
        dhash, phash, width, height, sharpness, taken_at, camera.
    """
    if visual is None:
        return (None,) * 7
    return (
        f"{visual.dhash:016x}",
        f"{visual.phash:016x}",
        visual.width,
        visual.height,
        visual.sharpness,
        visual.taken_at,
        visual.camera,
    )


def _visual_of(values: Sequence[object]) -> VisualFacts | None:
    """Rebuild visual facts from the version 2 columns.

    Args:
        values: dhash, phash, width, height, sharpness, taken_at, camera.

    Returns:
        The facts, or None when the image has none.
    """
    dhash, phash, width, height, sharpness, taken_at, camera = values
    if not isinstance(dhash, str) or not isinstance(phash, str):
        return None
    return VisualFacts(
        dhash=int(dhash, _HEX),
        phash=int(phash, _HEX),
        width=int(str(width)),
        height=int(str(height)),
        sharpness=float(str(sharpness)),
        taken_at=_text(taken_at),
        camera=_text(camera),
    )


def _metadata_of(value: object) -> MediaMetadata | None:
    """Read the metadata column.

    Args:
        value: The JSON text, or NULL.

    Returns:
        The metadata, or None when absent or unreadable.
    """
    if not isinstance(value, str):
        return None
    try:
        return MediaMetadata.model_validate_json(value)
    except ValidationError:
        return None


def _version(value: object) -> int:
    """Read the metadata version column.

    Args:
        value: The column.

    Returns:
        The version, 0 when unset.
    """
    return value if isinstance(value, int) else 0


def _text(value: object) -> str | None:
    """Read a nullable text column.

    Args:
        value: The column.

    Returns:
        The text, or None.
    """
    return value if isinstance(value, str) else None
