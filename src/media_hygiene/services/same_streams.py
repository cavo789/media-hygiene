"""Hash the picture and sound of re-encoded videos that may only differ by metadata.

Only the copies whose picture and sound boxes have the keeper's very size are read:
re-encoded copies never do, so this costs nothing in most libraries. The index keeps
each digest (`index.measures`): an unchanged video is never read twice.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.index.measures import Measure
from media_hygiene.plan.same_stream import with_same_streams
from media_hygiene.scan.media_payload import payload_digest, payload_size

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.index.measures import MeasureStore
    from media_hygiene.plan.keeper import KeepPolicy
    from media_hygiene.plan.similar_models import NearDecision, SimilarFindings
    from media_hygiene.scan.models import MediaFile


def same_streams(
    similar: SimilarFindings, policy: KeepPolicy, store: MeasureStore
) -> SimilarFindings:
    """Let the usual keep rules choose between copies of the same picture and sound.

    Args:
        similar: The findings, holding the re-encoded video groups.
        policy: Protected folders and the usual keep rules.
        store: The index, which keeps the digests.

    Returns:
        The findings, those groups chosen again.
    """
    files = list(_alike(similar.videos))
    if not files:
        return similar
    known = store.known(files, Measure.STREAM, str)
    hashed = {
        file.path: digest
        for file in files
        if file.path not in known and (digest := payload_digest(file.path)) is not None
    }
    store.keep(files, Measure.STREAM, hashed)
    streams = known | hashed
    if not streams:
        return similar
    return replace(similar, videos=with_same_streams(similar.videos, streams, policy))


def _alike(decisions: Iterable[NearDecision]) -> Iterable[MediaFile]:
    """The videos whose picture and sound have the size of their keeper's.

    Args:
        decisions: The re-encoded video groups.

    Yields:
        Each video to hash, keepers included.
    """
    for decision in decisions:
        size = payload_size(decision.keeper.path)
        members = (*decision.removable, *decision.protected)
        alike = [file for file in members if size and payload_size(file.path) == size]
        if alike:
            yield decision.keeper
            yield from alike
