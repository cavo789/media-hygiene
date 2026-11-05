"""`import --pick` (0590): the files only a folder holds, as tiles, before the copy.

The folder is only read: a tile shows the file where it lies. The files left out are
written to `import-left-out.json` of the reports folder and read back at each answer;
stored by source path, so a file moved in the source is simply proposed again. *Copy*
states its count: the server refuses another count (the page was out of date). The
copy is `ImportService.execute`, journaled and proven, in a thread the page follows.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from threading import Lock
from typing import TYPE_CHECKING

from media_hygiene.errors import MediaHygieneError
from media_hygiene.review.home_fields import write_whole
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.import_pick_tiles import (
    LEFT_OUT_FILE,
    Copying,
    ImportDone,
    ImportPickState,
    import_tile,
    read_left_out,
    tile_key,
)
from media_hygiene.services.import_run import ImportService

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from media_hygiene.actions.copy_in import CopyJob
    from media_hygiene.services.import_plan import ImportPlan
    from media_hygiene.services.runtime import Runtime


@dataclass(slots=True)
class ImportDesk:
    """The plan of one opening of the page, and its one copy."""

    runtime: Runtime
    plan: ImportPlan
    _copying: Copying | None = None
    _result: ImportDone | None = None
    _failure: str = ""
    _lock: Lock = field(default_factory=Lock)

    @property
    def _file(self) -> Path:
        """The file of the choices.

        Returns:
            In the reports folder.
        """
        return self.runtime.locations.reports_dir / LEFT_OUT_FILE

    def _left(self) -> tuple[CopyJob, ...]:
        """The copies not made yet, read from the disk.

        Returns:
            Those whose target does not exist.
        """
        return tuple(job for job in self.plan.jobs if not job.target.exists())

    def state(self) -> ImportPickState:
        """Describe the page, read from the disk.

        Returns:
            The state.
        """
        left_out = read_left_out(self._file)
        mapper = self.runtime.mapper
        copying = self._copying
        return ImportPickState(
            tiles=tuple(import_tile(job, mapper, left_out) for job in self._left()),
            copying=copying is not None,
            done=copying.done if copying else 0,
            total=copying.total if copying else 0,
            result=self._result,
            failure=self._failure,
        )

    def on_disk(self) -> ImportPickState:
        """The state, as `file_response` reads it.

        Returns:
            The state.
        """
        return self.state()

    def preview_source(self, key: str) -> Path | None:
        """The file of a tile, where it lies in the folder.

        Args:
            key: The tile's key.

        Returns:
            The file; None for a key of no file of the plan.
        """
        jobs = (job for job in self.plan.jobs if tile_key(job.source) == key)
        return next((job.source for job in jobs), None)

    def choose(self, keys: Iterable[str], *, out: bool) -> ImportPickState:
        """Leave files out or bring them back, then read the file back.

        Args:
            keys: The tiles picked.
            out: True to leave them out.

        Returns:
            The state, read again from the disk.
        """
        known = {tile_key(job.source): str(job.source) for job in self.plan.jobs}
        chosen = {known[key] for key in keys if key in known}
        before = read_left_out(self._file)
        after = before | chosen if out else before - chosen
        write_whole(self._file, json.dumps(sorted(after), ensure_ascii=False) + "\n")
        return self.state()

    def kept(self) -> tuple[CopyJob, ...]:
        """The copies *Copy* would make now.

        Returns:
            The files not copied yet and not left out.
        """
        left_out = read_left_out(self._file)
        return tuple(job for job in self._left() if str(job.source) not in left_out)

    def claim(self, count: int) -> tuple[CopyJob, ...] | None:
        """Take the copy, when no other runs and the count stated is the true one.

        Args:
            count: What the button said.

        Returns:
            The copies; None when refused.
        """
        with self._lock:
            jobs = self.kept()
            if self._copying is not None or count != len(jobs) or not jobs:
                return None
            self._copying = Copying(total=len(jobs))
            self._result = None
            self._failure = ""
            return jobs

    def copy(self, jobs: tuple[CopyJob, ...]) -> None:
        """Make the copies claimed: journaled, proven; runs in its own thread.

        Args:
            jobs: What `claim` gave.
        """
        service = ImportService(self.runtime, self._copying or NullProgress())
        try:
            result = service.execute(replace(self.plan, jobs=jobs), lambda: False)
        except (MediaHygieneError, OSError) as exc:
            self._failure = str(exc)
        else:
            self._result = ImportDone(
                run_id=result.run_id,
                copied=len(result.copied),
                failed=len(jobs) - len(result.copied),
            )
        finally:
            self._copying = None
