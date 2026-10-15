"""Near duplicates share one description: the version the audit keeps answers for them.

A WhatsApp copy and its original look alike: the model sees the version kept, and its
copies take its `vision` and `caption` tags, as identical copies and burst shots do
(`selection.vision_plan`). The groups are found again from the index, as the audit finds
them (`plan.similar.find_similar`: one copy per set of identical files, bursts apart,
then the colours the index measured). The `review --near` decisions win: `leave`
dissolves a group, each file then described on its own; `swap` makes the copy chosen
answer. A copy too small to be sent inherits too; a version that cannot be sent (too
small, a video without `ffmpeg`) answers for nobody.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import TYPE_CHECKING

from media_hygiene.plan.near_review import NearAction
from media_hygiene.plan.similar import SimilarInputs, find_similar
from media_hygiene.scan.filters import media_kind
from media_hygiene.scan.models import DuplicateGroup, MediaFile

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.plan.keeper import KeepPolicy
    from media_hygiene.plan.near_review import NearVerdict
    from media_hygiene.plan.similar_models import NearDecision
    from media_hygiene.scan.video_models import VideoLook
    from media_hygiene.tags.selection import VisionPlan


@dataclass(frozen=True, slots=True)
class NearSearch:
    """What finding the groups needs from the index, and the decisions of the review."""

    policy: KeepPolicy
    # The looks of the videos among these files (empty: no video is seen).
    looks: Callable[[Sequence[MediaFile]], Mapping[Path, VideoLook]]
    # The colourfulness the audits measured, by path.
    colours: Callable[[Sequence[MediaFile]], Mapping[Path, float]]
    # The decision of `review --near` on a group; None: undecided.
    verdict: Callable[[NearDecision], NearVerdict | None]


def near_shared(
    plan: VisionPlan, files: Sequence[MediaInput], search: NearSearch
) -> VisionPlan:
    """Let the version kept of each group of near duplicates answer for its copies.

    Args:
        plan: Who answers for whom: identical copies and bursts grouped.
        files: The files of the run.
        search: The index and the decisions.

    Returns:
        The plan, the copies answered by their group's version kept.
    """
    sets = _identical(files)
    redirect: dict[Path, Path] = {}  # a photo asked → the one asked instead
    inherit: dict[Path, Path] = {}  # a photo never sent → the one it takes after
    for group in _groups(files, search):
        answerer = _answerer(group, search)
        target = None if answerer is None else plan.answered_by.get(answerer.path)
        if target is None:
            continue
        for member in (group.keeper, *group.removable, *group.protected):
            for path in sets[member.path]:
                leader = plan.answered_by.get(path)
                if leader is None:
                    inherit[path] = target
                elif leader != target:
                    redirect[leader] = target
    if not redirect and not inherit:
        return plan
    answered = {
        path: redirect.get(leader, leader) for path, leader in plan.answered_by.items()
    }
    return replace(
        plan,
        asked=tuple(file for file in plan.asked if file.path not in redirect),
        answered_by=MappingProxyType(answered | inherit),
    )


def _answerer(group: NearDecision, search: NearSearch) -> MediaFile | None:
    """The version that answers for a group, as the review decided.

    Args:
        group: The group, as the audit plans it.
        search: The decisions.

    Returns:
        The copy chosen by a swap, else the version the audit keeps; None for a
        group left alone.
    """
    verdict = search.verdict(group)
    if verdict is None:
        return group.keeper
    if verdict.action is NearAction.LEAVE:
        return None
    return verdict.keep or group.keeper


def _identical(files: Sequence[MediaInput]) -> dict[Path, tuple[Path, ...]]:
    """Every file with its identical copies (itself included).

    Args:
        files: The files of the run.

    Returns:
        Each path → the paths sharing its content.
    """
    copies: dict[str, list[Path]] = {}
    for file in files:
        copies.setdefault(file.digest or str(file.path), []).append(file.path)
    return {path: tuple(group) for group in copies.values() for path in group}


def _groups(
    files: Sequence[MediaInput], search: NearSearch
) -> tuple[NearDecision, ...]:
    """Find the groups of near duplicates and re-encoded videos as the audit does.

    Hashes first, then again with the colours the audits measured on the versions
    found alike: a black and white edit stays apart from its colour original.

    Args:
        files: The files of the run.
        search: The index and the keep rules.

    Returns:
        The groups, pictures then videos.
    """
    pairs = [
        (file.digest, MediaFile(file.path, file.size, file.mtime_ns, kind))
        for file in files
        if (kind := media_kind(file.path)) is not None
    ]
    listed = [listed_file for _, listed_file in pairs]
    copies: dict[str, list[MediaFile]] = {}
    for digest, listed_file in pairs:
        if digest:
            copies.setdefault(digest, []).append(listed_file)
    inputs = SimilarInputs(
        files=listed,
        visuals=MappingProxyType({f.path: f.visual for f in files if f.visual}),
        groups=[
            DuplicateGroup(digest, group[0].size, tuple(group))
            for digest, group in copies.items()
            if len(group) > 1
        ],
        videos=search.looks(listed),
    )
    first = find_similar(inputs, search.policy).groups
    known = search.colours(list(_members(first)))
    if not known:
        return first
    coloured = replace(
        inputs,
        visuals=MappingProxyType(
            {
                path: replace(visual, colour=known.get(path))
                for path, visual in inputs.visuals.items()
            }
        ),
        videos=MappingProxyType(
            {
                path: replace(look, colour=known.get(path))
                for path, look in inputs.videos.items()
            }
        ),
    )
    return find_similar(coloured, search.policy).groups


def _members(groups: Iterable[NearDecision]) -> Iterable[MediaFile]:
    """Every version of every group, kept or not.

    Args:
        groups: The groups.

    Yields:
        The versions.
    """
    for group in groups:
        yield group.keeper
        yield from group.removable
        yield from group.protected
