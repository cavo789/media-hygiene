"""What the page of `review --pairs` receives: each folder pair, its evidence."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from media_hygiene.paths.host_paths import is_within
from media_hygiene.report.pair_views import pair_samples
from media_hygiene.report.reasons import keep_reason_label
from media_hygiene.review.near_views import folder_and_name
from media_hygiene.review.views import ORIGINAL_PREFIX, PREVIEW_PREFIX, preview_key

if TYPE_CHECKING:
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.plan.keeper import KeepPolicy
    from media_hygiene.plan.pairs import FolderPair
    from media_hygiene.scan.models import MediaFile

_FROZEN = ConfigDict(frozen=True, extra="forbid")


class SampleState(BaseModel):
    """One sample picture of a pair: the kept file, previewed."""

    model_config = _FROZEN

    name: str
    preview: str
    original: str


class PairState(BaseModel):
    """One folder pair: where the copies stay, where they go from, and the choice."""

    model_config = _FROZEN

    kept_in: str
    removed_from: str
    files: int
    size: int
    complete: bool  # the folder losing its copies holds nothing else analysed
    reasons: tuple[str, ...]  # why `kept_in` keeps the copies, most frequent first
    samples: tuple[SampleState, ...]
    swappable: bool  # not inside one folder, and `kept_in` is not protected
    action: str = ""  # empty: undecided; else a `PairAction`


class PairsReviewState(BaseModel):
    """Everything the page needs: `GET /api/state`."""

    model_config = _FROZEN

    decisions_file: str
    decisions_place: str
    pairs: tuple[PairState, ...]


def pair_swappable(pair: FolderPair, policy: KeepPolicy) -> bool:
    """Tell whether a pair may keep the copies of `removed_from` instead.

    The same rule as `clean --decisions`: not inside one folder, and `kept_in` not in
    a protected folder.

    Args:
        pair: The folder pair.
        policy: The keep policy, holding the protected folders.

    Returns:
        True when a swap is allowed.
    """
    if pair.kept_in == pair.removed_from:
        return False
    return not any(is_within(pair.kept_in, folder) for folder in policy.protected)


@dataclass(frozen=True, slots=True)
class PairsStateBuilder:
    """Describes the folder pairs of the audit for the page, in host paths."""

    mapper: HostPathMapper
    policy: KeepPolicy

    def pair(self, pair: FolderPair) -> PairState:
        """Describe one pair, undecided.

        Args:
            pair: The folder pair, as the audit plans it.

        Returns:
            Its state.
        """
        reasons = Counter(copy.reason for copy in pair.copies if copy.reason)
        return PairState(
            kept_in=self.mapper.to_host(pair.kept_in),
            removed_from=self.mapper.to_host(pair.removed_from),
            files=pair.files,
            size=pair.size,
            complete=pair.complete,
            reasons=tuple(
                keep_reason_label(reason) for reason, _count in reasons.most_common()
            ),
            samples=tuple(self.sample(file) for file in pair_samples(pair)),
            swappable=pair_swappable(pair, self.policy),
        )

    def sample(self, file: MediaFile) -> SampleState:
        """Describe one sample picture.

        Args:
            file: The kept file.

        Returns:
            Its state: name, preview and original links.
        """
        key = preview_key(file)
        _folder, name = folder_and_name(self.mapper.to_host(file.path))
        return SampleState(
            name=name,
            preview=f"{PREVIEW_PREFIX}{key}.jpg",
            original=f"{ORIGINAL_PREFIX}{key}{file.path.suffix.lower()}",
        )
