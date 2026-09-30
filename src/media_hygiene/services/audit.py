"""The audit use case: list, check, hash and plan — never modifies `/data`."""

from __future__ import annotations

import asyncio
import shutil
import time
from collections import Counter
from dataclasses import replace
from types import MappingProxyType
from typing import TYPE_CHECKING

from media_hygiene.constants import FFPROBE_BINARY
from media_hygiene.i18n import _
from media_hygiene.index.pruning import WalkCoverage, forget_missing
from media_hygiene.index.repository import FactsRepository
from media_hygiene.plan.models import AuditFindings
from media_hygiene.plan.orphans import sidecars_in_scope
from media_hygiene.plan.planner import build_plan
from media_hygiene.plan.similar import SimilarInputs, find_similar
from media_hygiene.scan.aliases import unique_files
from media_hygiene.scan.broken import BrokenFileFinder, IntegrityFindings
from media_hygiene.scan.deps import IntegrityTools, ScanDeps
from media_hygiene.scan.exact import ExactDuplicateFinder
from media_hygiene.scan.inventory import take_inventory
from media_hygiene.scan.progress import Step
from media_hygiene.scan.sidecars import accompanied
from media_hygiene.scan.walker import Walk, walk
from media_hygiene.services.data_checks import (
    refuse_empty_data,
    refuse_overlapping_mounts,
    warn_about_aliases,
    warn_about_scope,
)
from media_hygiene.services.policy import keep_policy, scan_filters

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.scan.filters import ScanFilters
    from media_hygiene.scan.models import DuplicateGroup, MediaFile
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime


class AuditService:
    """Runs a complete, read-only audit."""

    def __init__(self, runtime: Runtime, progress: ProgressSink) -> None:
        """Prepare an audit.

        Args:
            runtime: Settings, mount points and output.
            progress: Where to report progress.
        """
        self._runtime = runtime
        self._progress = progress

    def run(self) -> AuditFindings:
        """List media files, find broken files, exact duplicates and orphan sidecars.

        Returns:
            The findings and the plan.

        Raises:
            MountError: Nothing is mounted under the data directory, or a folder is
                mounted twice.
        """
        runtime, started = self._runtime, time.monotonic()
        refuse_empty_data(runtime)
        data_dir = runtime.locations.data_dir
        refuse_overlapping_mounts(runtime)
        warn_about_scope(runtime)
        roots = runtime.mounts.data_roots(data_dir)
        filters = scan_filters(runtime.settings, runtime.mapper)
        found = self._list_files(roots, filters)
        listed = frozenset(str(file.path) for file in found.files)
        groups, integrity = self._check_files(
            found, WalkCoverage(roots, listed, found.unreadable, filters)
        )
        policy = keep_policy(
            runtime.settings, runtime.mapper, accompanied(found.sidecars)
        )
        plan = build_plan(groups, integrity.broken, policy)
        # With --ext, sidecars already alone before the clean are left where they are.
        sidecars = sidecars_in_scope(
            found.sidecars, policy, alone=not runtime.settings.scan.extensions
        )
        return AuditFindings(
            roots=roots,
            plan=replace(plan, sidecars=sidecars),
            seconds=time.monotonic() - started,
            folder_files=MappingProxyType(
                Counter(file.path.parent for file in found.files)
            ),
            groups=groups,
            similar=find_similar(
                SimilarInputs(found.files, integrity.visuals, groups), policy
            ),
            inventory=take_inventory(found.files, integrity),
        )

    def _check_files(
        self, found: Walk, coverage: WalkCoverage
    ) -> tuple[tuple[DuplicateGroup, ...], IntegrityFindings]:
        """Forget from the index what is gone, then check and hash every file listed.

        Args:
            found: What the walk listed.
            coverage: What the walk could see, to tell which files are gone.

        Returns:
            The duplicate groups, the broken files and what files say of themselves.
        """
        runtime = self._runtime
        ffprobe = shutil.which(FFPROBE_BINARY)
        if ffprobe is None:
            runtime.output.warning(_("ffprobe not found: videos are not checked."))
        with (
            FactsRepository.open(runtime.index_file) as repository,
            runtime.executor_factory() as executor,
        ):
            forget_missing(repository, coverage)
            deps = ScanDeps(repository, self._progress)
            return asyncio.run(
                _analyse(
                    found.files,
                    BrokenFileFinder(deps, IntegrityTools(executor, ffprobe)),
                    ExactDuplicateFinder(deps),
                ),
            )

    def _list_files(self, roots: tuple[Path, ...], filters: ScanFilters) -> Walk:
        """Walk every root, without listing a file twice (nested mounts, hard links).

        Args:
            roots: Mounted folders.
            filters: Folders to skip and extensions to keep.

        Returns:
            The media files, by path, every sidecar found, what could not be read.
        """
        step = Step(
            _("Listing media files"),
            _(
                "Walks through every folder; photos and videos are recognised by their "
                "extension."
            ),
        )
        self._progress.start(step, None)
        found = asyncio.run(walk(roots, filters, self._progress))
        self._progress.stop()
        unique = unique_files(found.files)
        warn_about_aliases(self._runtime, unique.aliases)
        return Walk(unique.files, found.sidecars, found.unreadable)


async def _analyse(
    files: Sequence[MediaFile],
    broken_finder: BrokenFileFinder,
    exact_finder: ExactDuplicateFinder,
) -> tuple[tuple[DuplicateGroup, ...], IntegrityFindings]:
    """Find broken files first (describing images), then exact duplicates.

    Broken and empty files are kept out of duplicate groups: they are handled on their
    own (deleted when empty, quarantined when unreadable).

    Args:
        files: Every media file found.
        broken_finder: Integrity checker.
        exact_finder: Duplicate finder.

    Returns:
        The duplicate groups, the broken files and the visual facts of images.
    """
    integrity = await broken_finder.find(files)
    broken_paths = {item.file.path for item in integrity.broken}
    healthy = [
        file for file in files if file.size > 0 and file.path not in broken_paths
    ]
    return await exact_finder.find(healthy), integrity
