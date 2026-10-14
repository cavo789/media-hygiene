"""The classify use case: the walk and index of `audit`, then one proposal per file.

Read-only: `:ro` data mounts are fine. After an audit, nothing is decoded again: the
dates, cameras and metadata come from the index.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.whereabouts import load_towns
from media_hygiene.constants import MediaKind
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.index.pruning import WalkCoverage, forget_missing
from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan.aliases import unique_files
from media_hygiene.scan.broken import BrokenFileFinder
from media_hygiene.scan.deps import ScanDeps
from media_hygiene.scan.progress import Step
from media_hygiene.services.check_tools import check_tools
from media_hygiene.services.classify_inputs import (
    ClassifyInputs,
    duplicates,
    media_input,
    mounted,
    root_of,
)
from media_hygiene.services.classify_people import with_people
from media_hygiene.services.data_checks import refuse_empty_data
from media_hygiene.services.listing import list_media, tell_followed
from media_hygiene.services.policy import scan_filters

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.classify.ai.models import Subject
    from media_hygiene.classify.engine import Classification
    from media_hygiene.classify.models import MediaInput
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime

_SORTED_KINDS = frozenset({MediaKind.IMAGE, MediaKind.RAW, MediaKind.VIDEO})


@dataclass(frozen=True, slots=True)
class ClassifyResult:
    """The proposals, and the exact duplicates that would be sorted twice."""

    classification: Classification
    duplicates: int
    narrowed: bool = False  # `--year` or `--path`: the other files got no proposal


class ClassifyService:
    """Proposes a tree; changes nothing."""

    def __init__(self, runtime: Runtime, progress: ProgressSink) -> None:
        """Prepare a classification.

        Args:
            runtime: Settings, mount points and output.
            progress: Where to report progress.
        """
        self._runtime = runtime
        self._progress = progress

    def run(self, years: tuple[int, int] | None = None) -> ClassifyResult:
        """Walk, check what the index lacks, and propose a place for every file.

        Args:
            years: Only the files dated in these years get a proposal.

        Returns:
            The proposals and the duplicates count.
        """
        return self.decide(self.collect(years))

    def collect(self, years: tuple[int, int] | None = None) -> ClassifyInputs:
        """Walk and check what the index lacks.

        Args:
            years: Only the files dated in these years get a proposal.

        Returns:
            The files and the scope.

        Raises:
            MountError: Nothing is mounted, or the target is not mounted.
        """
        runtime = self._runtime
        refuse_empty_data(runtime, "classify")
        data_dir = runtime.locations.data_dir
        roots = runtime.mounts.data_roots(data_dir)
        scope = with_people(self._scope(years), runtime)
        # A file already in the target reads its folders from there: a target inside
        # a mounted folder (`C:\\Photos\\Tri`) never becomes a category of its own.
        files = self._inputs(roots, (scope.target,) if scope.target else ())
        return ClassifyInputs(tuple(files), scope)

    def decide(
        self,
        inputs: ClassifyInputs,
        subjects: Mapping[str, Mapping[Path, Subject]] | None = None,
    ) -> ClassifyResult:
        """Propose a place for every file.

        Args:
            inputs: The files and the scope.
            subjects: What a local model said, by `subject` rule.

        Returns:
            The proposals and the duplicates count.
        """
        scope = replace(inputs.scope, seen=inputs.scope.seen.with_subjects(subjects))
        files = inputs.files
        return ClassifyResult(
            classify(files, self._runtime.settings.classify, scope),
            duplicates(files),
        )

    def _scope(self, years: tuple[int, int] | None) -> Scope:
        """Target root, folders never moved, years.

        Args:
            years: The years asked for.

        Returns:
            The scope, in container paths.

        Raises:
            MountError: The target is outside the mounted folders.
        """
        runtime = self._runtime
        settings, mapper = runtime.settings, runtime.mapper
        target = None
        if settings.classify.target:
            target = mapper.to_container(settings.classify.target)
            if not mounted(target, runtime.locations.data_dir):
                raise MountError(
                    _("The target {path} is not mounted.").format(
                        path=settings.classify.target
                    ),
                    _('Mount it under /data, e.g. -v "C:\\Photos triées:/data/c/Tri".'),
                )
        kept = (*settings.folders.protected, *settings.classify.leave)
        return Scope(
            target,
            tuple(mapper.to_container(p) for p in kept),
            years,
            settings.keep.generic_folders,
            mapper.to_host,
            towns=load_towns(settings.classify),
        )

    def _inputs(
        self, roots: tuple[Path, ...], target: tuple[Path, ...]
    ) -> list[MediaInput]:
        """List the media files with what the index knows of them.

        Args:
            roots: Mounted folders.
            target: The target root, if any: the root of the files already in it.

        Returns:
            One input per readable, non-empty photo, RAW file or video.
        """
        runtime = self._runtime
        filters = scan_filters(runtime.settings, runtime.mapper)
        self._progress.start(Step(_("Listing media files"), ""), None)
        found = list_media(runtime, roots, self._progress)
        self._progress.stop()
        files = [
            file
            for file in unique_files(found.files).files
            if file.kind in _SORTED_KINDS and file.size
        ]
        with (
            FactsRepository.open(runtime.index_file) as repository,
            runtime.executor_factory() as executor,
        ):
            listed = frozenset(str(file.path) for file in found.files)
            coverage = WalkCoverage(roots, listed, found.unreadable, filters, files)
            tell_followed(runtime, forget_missing(repository, coverage))
            repository.preload(roots)  # one read of the index, as the audit (0157)
            tools = check_tools(runtime, executor)
            finder = BrokenFileFinder(ScanDeps(repository, self._progress), tools)
            integrity = asyncio.run(finder.find(files))
            broken = {item.file.path for item in integrity.broken}
            return [
                media_input(
                    file, root_of(file.path, (*target, *roots), runtime), repository
                )
                for file in files
                if file.path not in broken
            ]
