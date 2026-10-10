"""How sure a group of near duplicates is: moved at once, or worth a look first.

A group is sure when every copy it moves is, for one of these reasons:

- a video with the very picture and sound of the kept one (its metadata alone differ);
- the same fingerprints (perceptual distance 0) and the same camera as the kept one;
- a smaller copy in a messaging or e-mail folder, with the same shooting date.

Every other group is to check: `clean --tier near` leaves it alone until a person
decides (`--tier near-all` moves it all the same).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Final

from media_hygiene.plan.similar_models import SureReason

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.plan.similar_models import NearDecision, SimilarFindings
    from media_hygiene.scan.models import MediaFile

# Folders where messaging apps and e-mail clients save what they receive or send.
MESSAGING_FOLDERS: Final = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"whatsapp( .*)?",
        r"telegram( .*)?",
        r"signal( .*)?",
        r"messenger",
        r"viber( .*)?",
        r"wechat( .*)?",
        r"e-?mails?",
        r"outlook",
        r"thunderbird",
        r".*attachments?",
        r"pi[eè]ces[ -]jointes",
    )
)
# From the most certain to the least: a group is as sure as its least sure copy.
_STRENGTH: Final = (
    SureReason.SAME_STREAM,
    SureReason.SAME_LOOK,
    SureReason.MESSAGING_COPY,
)


@dataclass(frozen=True, slots=True)
class CopyFacts:
    """What tells a copy from the kept version: its date, camera and fingerprints."""

    taken_at: str | None
    camera: str | None = None
    hashes: tuple[int, int] | None = None  # images only: dHash and pHash


type FactsOf = Callable[[MediaFile], CopyFacts]


def with_levels(similar: SimilarFindings) -> SimilarFindings:
    """Mark the sure groups of near duplicates and re-encoded videos.

    Args:
        similar: The findings, colours and same streams checked.

    Returns:
        The findings, each sure group with its reason.
    """

    def image(file: MediaFile) -> CopyFacts:
        """Describe an image.

        Args:
            file: The image.

        Returns:
            Its facts.
        """
        visual = similar.visuals[file.path]
        hashes = (visual.dhash, visual.phash)
        return CopyFacts(visual.taken_at, visual.camera, hashes)

    def video(file: MediaFile) -> CopyFacts:
        """Describe a video.

        Args:
            file: The video.

        Returns:
            Its facts.
        """
        return CopyFacts(similar.video_looks[file.path].recorded_at)

    return replace(
        similar,
        near=tuple(leveled(decision, image) for decision in similar.near),
        videos=tuple(leveled(decision, video) for decision in similar.videos),
    )


def leveled(decision: NearDecision, facts: FactsOf) -> NearDecision:
    """Mark a group sure when every copy it moves is.

    Args:
        decision: The group.
        facts: What tells a version from another.

    Returns:
        The group, with the reason of its least sure copy, or unchanged.
    """
    reasons = [copy_reason(decision, copy, facts) for copy in decision.removable]
    if not reasons or None in reasons:
        return replace(decision, sure=None)
    sure = max((r for r in reasons if r is not None), key=_STRENGTH.index)
    return replace(decision, sure=sure)


def copy_reason(
    decision: NearDecision, copy: MediaFile, facts: FactsOf
) -> SureReason | None:
    """Say why a copy needs no look, if it does not.

    Args:
        decision: Its group.
        copy: A copy the group moves.
        facts: What tells a version from another.

    Returns:
        The reason, or None for a copy to check.
    """
    if copy.path in decision.same_stream:
        return SureReason.SAME_STREAM
    kept, other = facts(decision.keeper), facts(copy)
    if (
        kept.hashes is not None
        and kept.hashes == other.hashes
        and kept.camera
        and kept.camera == other.camera
    ):
        return SureReason.SAME_LOOK
    if (
        kept.taken_at
        and kept.taken_at == other.taken_at
        and copy.size < decision.keeper.size
        and in_messaging_folder(copy.path)
    ):
        return SureReason.MESSAGING_COPY
    return None


def in_messaging_folder(path: Path) -> bool:
    """Tell whether a file lies in a folder of a messaging app or an e-mail client.

    Args:
        path: The file.

    Returns:
        True when one of its folders is named like one.
    """
    return any(
        pattern.fullmatch(folder)
        for folder in path.parent.parts
        for pattern in MESSAGING_FOLDERS
    )
