"""One duplicate group decided: the copy that stays and the copies that go."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from media_hygiene.constants import KeepReason
    from media_hygiene.scan.models import MediaFile


@dataclass(frozen=True, slots=True)
class KeepDecision:  # pylint: disable=too-many-instance-attributes
    """One duplicate group: the copy that stays and the copies that go.

    `protected` copies lie in protected folders; `spared` ones were kept by a review
    decision (`clean --decisions`). Neither is ever removed. `linked` copies keep
    their name, which becomes a hard link to `keeper` (a pair keeping both, 0213).
    """

    digest: str
    size: int
    keeper: MediaFile
    removable: tuple[MediaFile, ...]
    protected: tuple[MediaFile, ...] = ()
    reason: KeepReason | None = None
    spared: tuple[MediaFile, ...] = ()
    linked: tuple[MediaFile, ...] = ()

    @property
    def reclaimable(self) -> int:
        """Bytes freed by removing the removable copies.

        Returns:
            Size times the number of removable copies.
        """
        return self.size * len(self.removable)
