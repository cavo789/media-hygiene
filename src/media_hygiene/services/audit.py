"""The audit use case: list, check, hash and plan — never modifies `/data`."""

from __future__ import annotations

import asyncio
import time
from collections import Counter
from dataclasses import replace
from types import MappingProxyType
from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.index.measures import MeasureStore
from media_hygiene.index.pruning import WalkCoverage, forget_missing
from media_hygiene.index.repository import FactsRepository
from media_hygiene.plan.models import AuditFindings
from media_hygiene.plan.orphans import sidecars_in_scope
from media_hygiene.plan.planner import build_plan
from media_hygiene.plan.similar import SimilarInputs
from media_hygiene.scan.aliases import unique_files
from media_hygiene.scan.broken import BrokenFileFinder
from media_hygiene.scan.colour import ColourTools
from media_hygiene.scan.deps import ScanDeps
from media_hygiene.scan.exact import ExactDuplicateFinder
from media_hygiene.scan.inventory import take_inventory
from media_hygiene.scan.progress import Step
from media_hygiene.scan.sidecars import accompanied
from media_hygiene.scan.stopwatch import Stage, Stopwatch
from media_hygiene.scan.walker import Walk
from media_hygiene.services.audit_analysis import Finders, analyse
from media_hygiene.services.check_guide import CheckGuide
from media_hygiene.services.check_tools import audit_tools
from media_hygiene.services.data_checks import (
    refuse_empty_data,
    refuse_overlapping_mounts,
    warn_about_aliases,
    warn_about_scope,
)
from media_hygiene.services.listing import list_media, tell_followed
from media_hygiene.services.near_checks import NearTools, checked_similar
from media_hygiene.services.policy import keep_policy, scan_filters
from media_hygiene.tags.xmp_owner import with_edits

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.plan.keeper import KeepPolicy
    from media_hygiene.plan.similar_models import SimilarFindings
    from media_hygiene.scan.broken import IntegrityFindings
    from media_hygiene.scan.models import DuplicateGroup
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
        self._stopwatch = Stopwatch()
        self.guide = CheckGuide.of(runtime)  # told the pace of the checks, as they go

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
        data_dir = runtime.locations.data_dir
        refuse_overlapping_mounts(runtime)
        warn_about_scope(runtime)
        roots = runtime.mounts.data_roots(data_dir)
        filters = scan_filters(runtime.settings, runtime.mapper)
        with self._stopwatch.timing(Stage.LISTING):
            found, every_path = self._list_files(roots)
        listed = frozenset(str(file.path) for file in found.files)
        policy = keep_policy(
            runtime.settings, runtime.mapper, accompanied(with_edits(found.sidecars))
        )
        groups, integrity, similar = self._analyse_files(
            found,
            WalkCoverage(roots, listed, found.unreadable, filters, found.files),
            policy,
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
            similar=similar,
            inventory=take_inventory(found.files, integrity),
            listed=every_path,
            stages=self._stopwatch.times(),
            unread=integrity.unread,
        )

    def _analyse_files(
        self, found: Walk, coverage: WalkCoverage, policy: KeepPolicy
    ) -> tuple[tuple[DuplicateGroup, ...], IntegrityFindings, SimilarFindings]:
        """Forget what is gone, check and hash every file, then find near duplicates.

        One index connection and one pool serve every step.

        Args:
            found: What the walk listed.
            coverage: What the walk could see, to tell which files are gone.
            policy: Protected folders and the usual keep rules.

        Returns:
            The duplicate groups, the broken files and what files say of themselves,
            and the near duplicates.
        """
        with (
            FactsRepository.open(self._runtime.index_file) as repository,
            self._runtime.executor_factory() as executor,
        ):
            with self._stopwatch.timing(Stage.INDEX):
                tell_followed(self._runtime, forget_missing(repository, coverage))
                repository.preload(coverage.roots)
            deps = ScanDeps(repository, self._progress, reporter=self.guide)
            checks = audit_tools(self._runtime, executor)
            finders = Finders(
                BrokenFileFinder(deps, checks),
                ExactDuplicateFinder(deps),
                self._stopwatch,
            )
            groups, integrity = asyncio.run(analyse(found.files, finders))
            tools = NearTools(
                ColourTools(checks.ffmpeg, self._progress, executor),
                MeasureStore(repository.connection),
                self._stopwatch,
            )
            similar = checked_similar(
                SimilarInputs.of(found.files, integrity, groups), policy, tools
            )
        return groups, integrity, similar

    def _list_files(self, roots: tuple[Path, ...]) -> tuple[Walk, frozenset[Path]]:
        """Walk every root, without listing a file twice (nested mounts, hard links).

        Args:
            roots: Mounted folders.

        Returns:
            The media files, by path, every sidecar found, what could not be read;
            then every media path listed, the aliases set aside included.
        """
        step = Step(
            _("Listing media files"),
            _(
                "Walks through every folder; photos and videos are recognised by their "
                "extension."
            ),
        )
        self._progress.start(step, None)
        found = list_media(self._runtime, roots, self._progress)
        self._progress.stop()
        unique = unique_files(found.files)
        warn_about_aliases(self._runtime, unique.aliases)
        every_path = frozenset(file.path for file in found.files)
        return Walk(unique.files, found.sidecars, found.unreadable), every_path
