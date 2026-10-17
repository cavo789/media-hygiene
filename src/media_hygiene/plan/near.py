"""Near duplicates: one picture saved again at another size, quality or without EXIF.

Two images are near duplicates only when every test agrees: both 64-bit hashes differ
by at most `NEAR_DISTANCE` bits, the aspect ratio is the same (±1 %), and the smaller
one was shot at the same moment or has lost its date, and both keep the same colours
when they were measured (a black and white edit is not a copy). A burst (another
moment) never qualifies, nor a Google Photos edit and its original (`IMG_1-edited.jpg`
and `IMG_1.jpg`): an edit is a choice.
Featureless images (black, white, blank) are left out: they all hash alike.

Candidates meet through multi-index hashing: two hashes at most 3 bits apart share at
least one of their four 16-bit quarters, so only images sharing a quarter are compared.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.plan.likeness import (
    distance,
    is_flat,
    same_aspect,
    same_colours,
)
from media_hygiene.plan.near_keeper import choose_keeper
from media_hygiene.plan.near_pairs import close_pairs
from media_hygiene.plan.near_rounds import Grouping, in_rounds
from media_hygiene.plan.union_find import UnionFind
from media_hygiene.scan.takeout import is_edit_pair

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.plan.keeper import KeepPolicy
    from media_hygiene.plan.near_keeper import NearChoice
    from media_hygiene.plan.similar_models import NearDecision
    from media_hygiene.scan.models import MediaFile, VisualFacts

NEAR_DISTANCE: Final = 2


def is_featureless(visual: VisualFacts) -> bool:
    """Tell whether an image has almost no detail (its gradient hash is nearly flat).

    Args:
        visual: What the image looks like.

    Returns:
        True for black, white or blank pictures.
    """
    return is_flat(visual.dhash)


def is_near(best: VisualFacts, other: VisualFacts) -> bool:
    """Tell whether `other` is a smaller or recompressed version of `best`.

    Args:
        best: The larger version.
        other: The candidate copy.

    Returns:
        True when every test agrees.
    """
    return (
        distance(best.dhash, other.dhash) <= NEAR_DISTANCE
        and distance(best.phash, other.phash) <= NEAR_DISTANCE
        and same_aspect((best.width, best.height), (other.width, other.height))
        and (other.taken_at is None or other.taken_at == best.taken_at)
        and same_colours(best.colour, other.colour)
    )


def near_decisions(
    files: Sequence[MediaFile],
    visuals: Mapping[Path, VisualFacts],
    policy: KeepPolicy,
) -> tuple[NearDecision, ...]:
    """Group near duplicates and choose the version to keep in each group.

    The highest resolution is kept, then a file larger by 1 % or more, then the usual
    keep rules (`near_keeper`).
    Only copies near the kept version are listed; protected copies are never removable.
    The rest of a group, and the chains its copies held together, are settled in
    rounds (`near_rounds`): a second audit after cleaning finds nothing new.

    Args:
        files: Candidate images, one per exact-duplicate group.
        visuals: What each image looks like.
        policy: Protected folders and the usual keep rules.

    Returns:
        The decisions, the largest keeper first.
    """
    usable = [
        file
        for file in files
        if file.path in visuals and not is_featureless(visuals[file.path])
    ]
    grouping = Grouping(
        clusters=lambda left: _clusters(left, visuals),
        settle=lambda cluster: _settle(cluster, visuals, policy),
        policy=policy,
    )
    return in_rounds(usable, grouping)


def _settle(
    cluster: list[MediaFile],
    visuals: Mapping[Path, VisualFacts],
    policy: KeepPolicy,
) -> tuple[NearChoice, list[MediaFile]]:
    """Choose the version to keep among linked images, and find its near copies.

    Args:
        cluster: Linked images, two or more.
        visuals: What each one looks like.
        policy: Protected folders and the usual keep rules.

    Returns:
        The version kept and why, and the copies near it.
    """
    choice = choose_keeper(cluster, lambda file: visuals[file.path].pixels, policy)
    best = visuals[choice.keeper.path]
    near = [
        file
        for file in cluster
        if file != choice.keeper
        and is_near(best, visuals[file.path])
        and not is_edit_pair(file.path.name, choice.keeper.path.name)
    ]
    return choice, near


def _clusters(
    files: Sequence[MediaFile], visuals: Mapping[Path, VisualFacts]
) -> Iterable[list[MediaFile]]:
    """Link images whose hashes are close, and return the linked sets.

    Args:
        files: Candidate images.
        visuals: What each image looks like.

    Returns:
        The sets of two images or more.
    """
    links = UnionFind(files)
    if len(files) < 2:  # noqa: PLR2004 - a pair needs two
        return links.sets()
    firsts, seconds = close_pairs([visuals[file.path] for file in files], NEAR_DISTANCE)
    for first, second in zip(firsts.tolist(), seconds.tolist(), strict=True):
        if not is_edit_pair(files[first].path.name, files[second].path.name):
            links.link(first, second)
    return links.sets()
