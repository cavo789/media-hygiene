"""What `tags` needs to let near duplicates share one description: index and decisions.

The groups are those of the audit, found again from the index (`tags.near_share`); the
decisions are those of the last `review --near`: `decisions.json` in the reports
folder, else the newest file `clean --decisions` archived (`decisions.applied-*.json`),
so that a group left alone stays apart once the clean applied the file. Without a
readable file, every group is described through the version the audit keeps; the
verbose log says why.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.constants import MediaKind
from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.index.measures import Measure, MeasureStore
from media_hygiene.plan.near_review import NearAction, NearVerdict
from media_hygiene.report.decisions import read_decisions
from media_hygiene.review.near_file import decision_key, group_key
from media_hygiene.review.place import DEFAULT_DECISIONS
from media_hygiene.scan.video_prints import look_of
from media_hygiene.services.policy import keep_policy
from media_hygiene.tags.near_share import NearSearch

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from media_hygiene.index.repository import FactsRepository
    from media_hygiene.plan.similar_models import NearDecision
    from media_hygiene.report.near_decisions import NearGroupDecision
    from media_hygiene.review.near_file import GroupKey
    from media_hygiene.scan.models import MediaFile
    from media_hygiene.scan.video_models import VideoLook
    from media_hygiene.services.runtime import Runtime

_APPLIED: Final = "decisions.applied-*.json"  # `services.decisions_archive`


def near_search(
    runtime: Runtime, repository: FactsRepository, *, videos: bool
) -> NearSearch:
    """Bind the near-duplicate search of `tags` to the index and the decisions.

    Args:
        runtime: Settings, mount points and output.
        repository: The open index.
        videos: Whether the model sees videos (`ffmpeg` is there).

    Returns:
        The search.
    """
    decided = _decided(runtime)
    mapper = runtime.mapper

    def verdict(group: NearDecision) -> NearVerdict | None:
        """The decision on a group, in container paths.

        Args:
            group: The group, as the audit plans it.

        Returns:
            The decision; None when undecided.
        """
        found = decided.get(group_key(mapper, group))
        if found is None or found.action is not NearAction.SWAP:
            return None if found is None else NearVerdict(found.action)
        keep = next(
            (f for f in group.removable if mapper.to_host(f.path) == found.keep), None
        )
        return NearVerdict(found.action, keep)

    def looks(files: Sequence[MediaFile]) -> Mapping[Path, VideoLook]:
        """The looks the index keeps of the videos among the files.

        Args:
            files: The candidates.

        Returns:
            Each fingerprinted video → its look; empty when no video is seen.
        """
        if not videos:
            return {}
        return {
            file.path: look
            for file in files
            if file.kind is MediaKind.VIDEO
            and (look := look_of(repository.get(file))) is not None
        }

    store = MeasureStore(repository.connection)
    return NearSearch(
        policy=keep_policy(runtime.settings, mapper),
        looks=looks,
        colours=lambda files: store.known(files, Measure.COLOUR, float),
        verdict=verdict,
    )


def _decided(runtime: Runtime) -> dict[GroupKey, NearGroupDecision]:
    """The `near` decisions of the last decisions file, by group.

    Args:
        runtime: Mount points and output.

    Returns:
        Each decided group; empty when there is no readable file.
    """
    output = runtime.output
    reports = runtime.locations.reports_dir
    target = _last_file(reports)
    shared = _("Each group of near duplicates is described through the version kept.")
    if target is None:
        if output.verbose:
            missing = _("No decisions file of 'review --near' in {folder}.")
            folder = runtime.mapper.to_host(reports)
            output.info(f"{missing.format(folder=folder)} {shared}")
        return {}
    try:
        decisions = read_decisions(target)
    except DecisionsError as exc:
        if output.verbose:
            output.info(f"{exc.message} {shared}")
        return {}
    return {decision_key(decision): decision for decision in decisions.near}


def _last_file(reports: Path) -> Path | None:
    """The decisions file not applied yet, else the newest one applied.

    Args:
        reports: The reports mount point.

    Returns:
        The file, or None when no review was saved there.
    """
    current = reports / DEFAULT_DECISIONS
    if current.is_file():
        return current
    applied = [path for path in reports.glob(_APPLIED) if path.is_file()]
    return max(applied, key=lambda path: path.stat().st_mtime_ns, default=None)
