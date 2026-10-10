"""Hash the picture and sound of re-encoded videos that may only differ by metadata.

Only the copies whose picture and sound boxes have the keeper's very size are read:
re-encoded copies never do, so this costs nothing in most libraries.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.plan.same_stream import with_same_streams
from media_hygiene.scan.media_payload import payload_digest, payload_size

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from media_hygiene.plan.keeper import KeepPolicy
    from media_hygiene.plan.similar_models import NearDecision, SimilarFindings


def same_streams(similar: SimilarFindings, policy: KeepPolicy) -> SimilarFindings:
    """Let the usual keep rules choose between copies of the same picture and sound.

    Args:
        similar: The findings, holding the re-encoded video groups.
        policy: Protected folders and the usual keep rules.

    Returns:
        The findings, those groups chosen again.
    """
    streams = dict(_digests(similar.videos))
    if not streams:
        return similar
    return replace(similar, videos=with_same_streams(similar.videos, streams, policy))


def _digests(decisions: Iterable[NearDecision]) -> Iterable[tuple[Path, str]]:
    """Hash the videos whose picture and sound have the size of their keeper's.

    Args:
        decisions: The re-encoded video groups.

    Yields:
        The path and digest of each video hashed, keepers included.
    """
    for decision in decisions:
        size = payload_size(decision.keeper.path)
        members = (*decision.removable, *decision.protected)
        alike = [file for file in members if size and payload_size(file.path) == size]
        if not alike:
            continue
        for file in (decision.keeper, *alike):
            if (digest := payload_digest(file.path)) is not None:
                yield file.path, digest
