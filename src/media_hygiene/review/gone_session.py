"""A `review --gone` in progress: the files gone answered, saved after every answer.

The decisions file is shared with the other reviews and `search`: this one keeps what
it finds there and writes the `gone` key, every file answered (deleted on purpose, or
moved elsewhere). Reopened, it resumes; an answer about a file no longer recorded as
gone is dropped. After each answer the file is read back from the disk: the page
shows what it holds, never its own memory.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.report.decisions import write_decisions
from media_hygiene.report.gone_decisions import GoneEntry
from media_hygiene.review.gone_file import FileKey, gone_proven, read_gone_back
from media_hygiene.review.gone_views import (
    GoneReviewState,
    GoneStateBuilder,
    gone_groups,
    gone_key,
    kept_preview,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.index.gone_rows import GoneRecord
    from media_hygiene.report.decisions import DecisionsFile
    from media_hygiene.review.gone_file import GoneProof
    from media_hygiene.review.place import DecisionsPlace

_DELETED, _MOVED = "deleted", "moved"


@dataclass(frozen=True, slots=True)
class GonePages:
    """What the review is about: the files gone, how to show them, the file to write."""

    records: tuple[GoneRecord, ...]
    builder: GoneStateBuilder
    target: Path
    place: DecisionsPlace


class GoneSession:
    """The files gone under review and the answers, in memory and on disk."""

    def __init__(self, source: GonePages, base: DecisionsFile) -> None:
        """Resume the answers of `base` that still match a file gone.

        Args:
            source: The files gone and the decisions file.
            base: What the decisions file holds already.
        """
        self._source = source
        self._base = base
        mapper = source.builder.mapper
        self._states = tuple(source.builder.file(r) for r in source.records)
        self._keys: dict[FileKey, int] = {
            (mapper.to_host(Path(r.path)), r.size, r.mtime_ns): rank
            for rank, r in enumerate(source.records)
        }
        self._previews = {gone_key(r): r for r in source.records}
        self._deleted: dict[int, bool] = {}
        self.dropped = 0
        for entry in base.gone:
            rank = self._keys.get((entry.path, entry.size, entry.mtime_ns))
            if rank is None:
                self.dropped += 1
                continue
            self._deleted[rank] = entry.deleted

    @property
    def place(self) -> DecisionsPlace:
        """The decisions file, for `clean --decisions` and on the host.

        Returns:
            Its names.
        """
        return self._source.place

    @property
    def decided(self) -> tuple[int, int, int]:
        """How far the review went.

        Returns:
            The files answered, those deleted on purpose, and every file.
        """
        deleted = sum(self._deleted.values())
        return len(self._deleted), deleted, len(self._states)

    def counts(self) -> dict[str, int]:
        """How far the review went, as the page reads it after each answer.

        Returns:
            `decided`, `deleted` and `total`.
        """
        decided, deleted, total = self.decided
        return {"decided": decided, "deleted": deleted, "total": total}

    def state(self) -> GoneReviewState:
        """Describe every file gone and the answers so far, for the page.

        Returns:
            The state.
        """
        answers = {
            rank: _DELETED if deleted else _MOVED
            for rank, deleted in self._deleted.items()
        }
        return GoneReviewState(
            decisions_file=self.place.argument,
            decisions_place=self.place.host,
            files=tuple(
                state.model_copy(update={"decision": answers.get(rank, "")})
                for rank, state in enumerate(self._states)
            ),
            groups=gone_groups(self._source.records, self._source.builder.mapper),
        )

    def preview_source(self, key: str) -> Path | None:
        """Find the preview the cache still holds of a file gone.

        Args:
            key: The preview key, from the page.

        Returns:
            The preview's file in the cache, or None.
        """
        record = self._previews.get(key)
        if record is None:
            return None
        return kept_preview(self._source.builder.previews, record)

    def save(self) -> None:
        """Write the decisions file: the files answered, in the review's order."""
        write_decisions(self._source.target, self.decisions())

    def on_disk(self) -> GoneProof:
        """Read the decisions file back from the disk.

        Returns:
            What it holds, file by file.

        Raises:
            DecisionsError: It cannot be read, or is not a decisions file.
        """
        return read_gone_back(self._source.target, self._keys)

    def decide(self, choices: Mapping[int, bool | None]) -> GoneProof:
        """Record answers, save them in one write, then read the file back.

        Args:
            choices: By file rank: True deleted on purpose, False moved elsewhere,
                None undecided again.

        Returns:
            Those files, as the file read back from the disk holds them.

        Raises:
            DecisionsError: An unknown file, or a file that does not hold the
                answers once saved.
        """
        if any(not 0 <= rank < len(self._states) for rank in choices):
            raise DecisionsError(_("There is no such file."))
        for rank, deleted in choices.items():
            if deleted is None:
                self._deleted.pop(rank, None)
            else:
                self._deleted[rank] = deleted
        self.save()
        return gone_proven(self.on_disk(), choices)

    def decisions(self) -> DecisionsFile:
        """Build the decisions file: what it held, the files answered in order.

        Returns:
            The decisions, in host paths.
        """
        keys = {rank: key for key, rank in self._keys.items()}
        listed = tuple(
            GoneEntry(
                path=keys[rank][0],
                size=keys[rank][1],
                mtime_ns=keys[rank][2],
                deleted=self._deleted[rank],
            )
            for rank in sorted(self._deleted)
        )
        return self._base.model_copy(update={"gone": listed})
