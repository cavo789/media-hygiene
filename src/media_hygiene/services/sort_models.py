"""What the sort use case hands the command line: a sort ready, then its result."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.manifest import Manifest
    from media_hygiene.actions.sort import MoveOutcome
    from media_hygiene.actions.sort_folders import FolderReport, FolderRules
    from media_hygiene.actions.sort_plan import SortPlan
    from media_hygiene.errors import MountError
    from media_hygiene.scan.stopwatch import StageTime
    from media_hygiene.services.sort_inputs import SortInputs


@dataclass(frozen=True, slots=True)
class Prepared:
    """A sort ready to run: its moves, and the folders it would remove."""

    inputs: SortInputs
    plan: SortPlan
    rules: FolderRules
    candidates: tuple[Path, ...]  # folders that may end up empty, deepest first
    folders: FolderReport  # the prediction
    seconds: float = 0.0  # what preparing it took, shown with the run's other stages


@dataclass(frozen=True, slots=True)
class SortResult:
    """What a sort run did, and the proof that nothing was lost."""

    run_id: str
    moves: MoveOutcome
    folders: FolderReport
    manifest: Manifest
    manifest_file: Path | MountError | None  # None: no /reports mount
    stages: tuple[StageTime, ...] = ()  # where the time went (`--verbosity verbose`)
