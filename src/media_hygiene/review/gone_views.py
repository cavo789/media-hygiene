"""What the page of `review --gone` receives: the files gone, grouped, previews kept.

The files are gone: a preview is shown only when the cache of previews still holds
one of that version of the file (a report or a review made it); else its name, date,
size and camera.
"""

from __future__ import annotations

import contextlib
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.constants import Sizes
from media_hygiene.i18n import _
from media_hygiene.report.preview_cache import PreviewJob, preview_key
from media_hygiene.report.thumbnails import REVIEW_EDGE
from media_hygiene.review.file_card import FileCard
from media_hygiene.review.near_views import folder_and_name
from media_hygiene.review.views import PREVIEW_PREFIX

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.index.gone_rows import GoneRecord
    from media_hygiene.paths.host_paths import HostPathMapper

_FROZEN = ConfigDict(frozen=True, extra="forbid")
# Files on one screen: a folder with thousands of files gone is shown page by page.
GROUP_SIZE: Final = 40
_KEY_LENGTH: Final = 24
# The previews a report (thumbnail) or a review made, the larger first.
_EDGES: Final = (REVIEW_EDGE, Sizes.THUMBNAIL_EDGE)


class GoneState(FileCard):
    """One file gone as the page shows it (no preview kept: empty), its answer."""

    decision: str = ""  # empty: undecided; `deleted` or `moved`


class GoneGroupState(BaseModel):
    """Files gone shown together: one folder, one day found gone (or a page of it)."""

    model_config = _FROZEN

    title: str
    files: tuple[int, ...]  # ranks in `GoneReviewState.files`


class GoneReviewState(BaseModel):
    """Everything the page needs: `GET /api/state`."""

    model_config = _FROZEN

    decisions_file: str
    decisions_place: str
    files: tuple[GoneState, ...]
    groups: tuple[GoneGroupState, ...]


def gone_key(record: GoneRecord) -> str:
    """Name the preview of a file gone: stable, safe in a URL.

    Args:
        record: The file, as the index knew it.

    Returns:
        The key.
    """
    identity = f"{record.path}\0{record.size}\0{record.mtime_ns}"
    return hashlib.sha256(identity.encode()).hexdigest()[:_KEY_LENGTH]


def kept_preview(folder: Path | None, record: GoneRecord) -> Path | None:
    """The preview of that version of the file, if the cache still holds one.

    Args:
        folder: The cache folder of previews, or None.
        record: The file gone.

    Returns:
        The preview's file in the cache, or None.
    """
    if folder is None:
        return None
    for edge in _EDGES:
        job = PreviewJob(Path(record.path), edge, folder)
        kept = folder / preview_key(job, record.size, record.mtime_ns)
        with contextlib.suppress(OSError):
            if kept.stat().st_size:  # empty: that version could not be shown
                return kept
    return None


def gone_groups(
    records: Sequence[GoneRecord], mapper: HostPathMapper
) -> tuple[GoneGroupState, ...]:
    """Group the files by folder and by day found gone, pages of `GROUP_SIZE` at most.

    Args:
        records: The files gone, in the order of the page.
        mapper: Container to host path translator.

    Returns:
        The groups, in the order of the files.
    """
    ranks: dict[tuple[str, str], list[int]] = {}
    for rank, record in enumerate(records):
        folder, _name = folder_and_name(mapper.to_host(Path(record.path)))
        ranks.setdefault((folder, record.gone_at[:10]), []).append(rank)
    groups: list[GoneGroupState] = []
    for (folder, day), members in ranks.items():
        for start in range(0, len(members), GROUP_SIZE):
            page = tuple(members[start : start + GROUP_SIZE])
            title = _("{folder} — gone since {day}: {first} to {last} of {total}")
            groups.append(
                GoneGroupState(
                    title=title.format(
                        folder=folder,
                        day=day,
                        first=human_number(start + 1),
                        last=human_number(start + len(page)),
                        total=human_number(len(members)),
                    ),
                    files=page,
                )
            )
    return tuple(groups)


def ordered(records: Sequence[GoneRecord]) -> tuple[GoneRecord, ...]:
    """Put the files of one folder and one day together, by name.

    Args:
        records: The files gone.

    Returns:
        Them, by folder, day found gone, then path.
    """
    return tuple(
        sorted(
            records, key=lambda r: (str(Path(r.path).parent), r.gone_at[:10], r.path)
        )
    )


@dataclass(frozen=True, slots=True)
class GoneStateBuilder:
    """Describes the files gone for the page, in host paths."""

    mapper: HostPathMapper
    previews: Path | None  # the cache folder of previews

    def file(self, record: GoneRecord) -> GoneState:
        """Describe one file gone, undecided.

        Args:
            record: The file, as the index knew it.

        Returns:
            Its state.
        """
        folder, name = folder_and_name(self.mapper.to_host(Path(record.path)))
        details = [record.taken_at or "", human_size(record.size), record.camera or ""]
        preview = ""
        if kept_preview(self.previews, record) is not None:
            preview = f"{PREVIEW_PREFIX}{gone_key(record)}.jpg"
        return GoneState(
            name=name,
            folder=folder,
            details=" · ".join(part for part in details if part),
            preview=preview,
        )
