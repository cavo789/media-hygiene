"""The audit use case: list, check, hash and plan — never modifies `/data`."""

from __future__ import annotations

import asyncio
import time
from collections import Counter
from dataclasses import replace
from types import MappingProxyType
from typing import TYPE_CHECKING

from media_hygiene.index.measures import MeasureStore
from media_hygiene.index.pruning import WalkCoverage, forget_missing
from media_hygiene.index.repository import FactsRepository
from media_hygiene.plan.face_scores import rank_by_faces
from media_hygiene.plan.models import AuditFindings
from media_hygiene.plan.orphans import sidecars_in_scope
from media_hygiene.plan.planner import build_plan
from media_hygiene.plan.returned import in_plan
from media_hygiene.plan.similar import SimilarInputs
from media_hygiene.scan.broken import BrokenFileFinder
from media_hygiene.scan.colour import ColourTools
from media_hygiene.scan.deps import ScanDeps
from media_hygiene.scan.exact import ExactDuplicateFinder
from media_hygiene.scan.intruders import outside
from media_hygiene.scan.inventory import take_inventory
from media_hygiene.scan.sidecars import accompanied
from media_hygiene.scan.stopwatch import Stage, Stopwatch
from media_hygiene.services.audit_analysis import Finders, analyse
from media_hygiene.services.audit_listing import list_walk
from media_hygiene.services.backup_dealt import gone_finder
from media_hygiene.services.check_guide import CheckGuide
from media_hygiene.services.check_tools import audit_tools
from media_hygiene.services.data_checks import (
    refuse_empty_data,
    refuse_overlapping_mounts,
    warn_about_scope,
)
from media_hygiene.services.listing import tell_followed
from media_hygiene.services.near_checks import NearTools, checked_similar
from media_hygiene.services.policy import backup_folders, keep_policy, scan_filters
from media_hygiene.services.returned import JournalFindings, returned_finder
from media_hygiene.tags.xmp_owner import with_edits

if TYPE_CHECKING:
    from media_hygiene.plan.backups import BackupComparison
    from media_hygiene.plan.keeper import KeepPolicy
    from media_hygiene.plan.similar_models import SimilarFindings
    from media_hygiene.scan.broken import IntegrityFindings
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.scan.walker import Walk
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
        self._stopwatch = Stopwatch()
        self.guide = CheckGuide.of(runtime)  # told the pace of the checks, as they go
        self._backups = backup_folders(runtime.settings, runtime.mapper)  # 0204

    def run(self) -> AuditFindings:
        """List media files, find broken files, exact duplicates and orphan sidecars.

        Returns:
            The findings and the plan.

        Raises:
            MountError: Nothing is mounted under the data directory, or a folder is
                mounted twice.
        """
        runtime, started = self._runtime, time.monotonic()
        refuse_empty_data(runtime, "audit")
        runtime.warm_pool()  # Pillow and numpy load while the folders are listed
        refuse_overlapping_mounts(runtime)
        warn_about_scope(runtime)
        roots = runtime.mounts.data_roots(runtime.locations.data_dir)
        filters = scan_filters(runtime.settings, runtime.mapper)
        with self._stopwatch.timing(Stage.LISTING):
            found, every_path = list_walk(runtime, roots, self._progress)
        library = self._backups.library(found)  # backups: compared, never changed
        policy = keep_policy(
            runtime.settings, runtime.mapper, accompanied(with_edits(library.sidecars))
        )
        compared, integrity, similar, back = self._analyse_files(
            library,
            WalkCoverage(
                roots,
                frozenset(str(file.path) for file in found.files),
                found.unreadable,
                filters,
                found.files,
                self._backups.folders,
            ),
            policy,
        )
        plan = build_plan(compared.groups, integrity.broken, policy)
        # With --ext, sidecars already alone before the clean are left where they are.
        sidecars = sidecars_in_scope(
            library.sidecars, policy, alone=not runtime.settings.scan.extensions
        )
        return AuditFindings(
            roots=roots,
            plan=replace(
                plan, sidecars=sidecars, returned=in_plan(back.returned, plan, policy)
            ),
            seconds=time.monotonic() - started,
            folder_files=MappingProxyType(
                Counter(file.path.parent for file in found.files)
            ),
            groups=compared.groups,
            similar=similar,
            inventory=take_inventory(library.files, integrity),
            listed=every_path,
            stages=self._stopwatch.times(),
            unread=integrity.unread,
            gone=back.gone,
            backups=compared.folders,
            intruders=outside(library.intruders, policy.protected),
        )

    def _analyse_files(
        self, found: Walk, coverage: WalkCoverage, policy: KeepPolicy
    ) -> tuple[
        BackupComparison,
        IntegrityFindings,
        SimilarFindings,
        JournalFindings,
    ]:
        """Forget what is gone, check and hash every file, then find near duplicates.

        One index connection and one pool serve every step.

        Args:
            found: What the walk listed, the backup folders left out.
            coverage: What the walk could see (backups included), to tell which
                files are gone.
            policy: Protected folders and the usual keep rules.

        Returns:
            The library's duplicate groups and what each backup lacks or holds
            alone, the broken files and what files say of themselves,
            the near duplicates; the files set aside before that came back, and
            how many files gone wait for `review --gone`.
        """
        with (
            FactsRepository.open(self._runtime.index_file) as repository,
            self._runtime.executor_factory() as executor,
        ):
            with self._stopwatch.timing(Stage.INDEX):
                pruned = forget_missing(repository, coverage)
                tell_followed(self._runtime, pruned)
                repository.preload(coverage.roots)
            deps = ScanDeps(repository, self._progress, reporter=self.guide)
            checks = audit_tools(self._runtime, executor)
            finders = Finders(
                BrokenFileFinder(deps, checks),
                ExactDuplicateFinder(deps),
                self._stopwatch,
                returned_finder(self._runtime, deps),
                self._backups,
                gone_finder(self._runtime, deps) if self._backups.folders else None,
            )
            compared, integrity, returned = asyncio.run(
                analyse(found.files, finders, coverage.files)
            )
            tools = NearTools(
                ColourTools(checks.ffmpeg, self._progress, executor),
                MeasureStore(repository.connection),
                self._stopwatch,
            )
            similar = checked_similar(
                SimilarInputs.of(found.files, integrity, compared.groups), policy, tools
            )
            similar = rank_by_faces(similar, repository.connection)
        return compared, integrity, similar, JournalFindings(returned, pruned.waiting)
