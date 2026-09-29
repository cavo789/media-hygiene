"""What the index remembers about one file version."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from media_hygiene.scan.metadata import METADATA_VERSION

if TYPE_CHECKING:
    from media_hygiene.constants import BrokenReason
    from media_hygiene.scan.metadata import MediaMetadata
    from media_hygiene.scan.models import VisualFacts


@dataclass(frozen=True, slots=True)
class Integrity:
    """The outcome of checking that a file can be read: healthy when no reason."""

    broken_reason: BrokenReason | None = None
    broken_detail: str = ""


@dataclass(frozen=True, slots=True)
class FileFacts:
    """Facts computed for a file at a given size and modification time."""

    partial_digest: str | None = None
    full_digest: str | None = None
    # None: never checked.
    integrity: Integrity | None = None
    visual_checked: bool = False
    visual: VisualFacts | None = None
    # 0: never read; older than METADATA_VERSION: read again once.
    metadata_version: int = 0
    metadata: MediaMetadata | None = None

    @property
    def integrity_checked(self) -> bool:
        """Tell whether the file was checked.

        Returns:
            True once an integrity check ran on this version of the file.
        """
        return self.integrity is not None

    @property
    def broken_reason(self) -> BrokenReason | None:
        """Why the file is broken.

        Returns:
            The reason, or None when healthy or never checked.
        """
        return self.integrity.broken_reason if self.integrity else None

    @property
    def broken_detail(self) -> str:
        """What the decoder said about a broken file.

        Returns:
            Its message, empty when healthy or never checked.
        """
        return self.integrity.broken_detail if self.integrity else ""

    def with_partial(self, digest: str) -> FileFacts:
        """Return a copy holding the partial digest.

        Args:
            digest: Partial SHA-256.

        Returns:
            The updated facts.
        """
        return replace(self, partial_digest=digest)

    def with_full(self, digest: str) -> FileFacts:
        """Return a copy holding the full digest.

        Args:
            digest: Full SHA-256.

        Returns:
            The updated facts.
        """
        return replace(self, full_digest=digest)

    def with_integrity(self, reason: BrokenReason | None, detail: str) -> FileFacts:
        """Return a copy holding the outcome of an integrity check.

        Args:
            reason: Why the file is broken, or None when healthy.
            detail: Decoder message, empty when healthy.

        Returns:
            The updated facts.
        """
        return replace(self, integrity=Integrity(reason, detail))

    def with_visual(self, visual: VisualFacts | None) -> FileFacts:
        """Return a copy holding what an image looks like (None when unreadable).

        Args:
            visual: The visual facts computed while decoding the image.

        Returns:
            The updated facts.
        """
        return replace(self, visual_checked=True, visual=visual)

    def with_metadata(self, metadata: MediaMetadata | None) -> FileFacts:
        """Return a copy holding what the file says about itself (None: nothing).

        Args:
            metadata: The metadata read while checking the file.

        Returns:
            The updated facts, marked as read by the current version.
        """
        return replace(self, metadata_version=METADATA_VERSION, metadata=metadata)
