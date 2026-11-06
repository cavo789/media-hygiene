"""A `review --junk` in progress: the photos decided, saved after every choice.

The decisions file is shared with the other reviews and `library`: this one writes the
`unwanted` key. Reopened, it resumes, even on a reason turned off since (0636); a
decision about a photo gone, or changed since (size, date), is dropped.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _
from media_hygiene.report.decisions import write_decisions
from media_hygiene.review.unwanted_file import (
    entry_key,
    photo_entry,
    photo_key,
    read_unwanted_back,
    unwanted_proven,
    with_decided,
)
from media_hygiene.review.unwanted_views import (
    UnwantedReviewState,
    photo_groups,
    reason_texts,
)
from media_hygiene.review.views import preview_key

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.config.review_settings import UnwantedSettings
    from media_hygiene.report.decisions import DecisionsFile
    from media_hygiene.review.place import DecisionsPlace
    from media_hygiene.review.strictness import Strictness
    from media_hygiene.review.unwanted_file import UnwantedPages, UnwantedProof

_ASIDE, _KEPT = "aside", "kept"


class UnwantedSession:  # pylint: disable=too-many-instance-attributes
    """The photos under review and the decisions, in memory and on disk."""

    def __init__(self, source: UnwantedPages, base: DecisionsFile) -> None:
        """Resume the decisions of `base` that still match a photo of the review.

        Args:
            source: The photos and the decisions file.
            base: What the decisions file holds already.
        """
        self.strictness: Strictness[UnwantedSettings] | None = None  # by the service
        self.dropped = 0
        self._load(source, base)

    def _load(self, source: UnwantedPages, base: DecisionsFile) -> None:
        """Index the photos and resume the decisions of `base` on them.

        Args:
            source: The photos and the decisions file.
            base: What the decisions file holds already.
        """
        self._source = source
        self._base = base
        mapper = source.builder.mapper
        self._states = tuple(source.builder.photo(photo) for photo in source.photos)
        self._keys = {photo_key(mapper, p): r for r, p in enumerate(source.photos)}
        self._previews = {preview_key(p.file): p.file.path for p in source.photos}
        self._aside: dict[int, bool] = {}
        for entry in base.unwanted:
            rank = self._keys.get(entry_key(entry))
            if rank is None:
                self.dropped += 1
                continue
            self._aside[rank] = entry.aside

    @property
    def place(self) -> DecisionsPlace:
        """The decisions file, for `clean --decisions` and on the host.

        Returns:
            Its names.
        """
        return self._source.place

    @property
    def decided(self) -> tuple[int, int, int]:
        """How far the review went.

        Returns:
            The photos decided, those set aside, and every photo.
        """
        aside = sum(self._aside.values())
        return len(self._aside), aside, len(self._states)

    def counts(self) -> dict[str, int]:
        """How far the review went, as the page reads it after each choice.

        Returns:
            `decided`, `aside` and `total`.
        """
        return dict(zip(("decided", "aside", "total"), self.decided, strict=True))

    def state(self) -> UnwantedReviewState:
        """Describe every photo and the decisions so far, for the page.

        Returns:
            The state.
        """
        decisions = {
            rank: _ASIDE if aside else _KEPT for rank, aside in self._aside.items()
        }
        return UnwantedReviewState(
            decisions_file=self.place.argument,
            decisions_place=self.place.host,
            photos=tuple(
                state.model_copy(update={"decision": decisions.get(rank, "")})
                for rank, state in enumerate(self._states)
            ),
            groups=photo_groups(self._source.photos),
            reasons=reason_texts(),
        )

    def retune(self, settings: UnwantedSettings) -> dict[str, str]:
        """List the photos again; a photo already decided stays listed, as decided.

        Args:
            settings: The thresholds.

        Returns:
            The file name of each photo the thresholds list, by path.
        """
        lister = self._source.lister
        photos = () if lister is None else lister(settings)
        every = with_decided(photos, self._source.photos, self._aside)
        self._load(replace(self._source, photos=every), self.decisions())
        return {str(photo.file.path): photo.file.path.name for photo in photos}

    def preview_source(self, key: str) -> Path | None:
        """Find the photo a preview or an original shows.

        Args:
            key: The preview key, from the page.

        Returns:
            The file, in the container, or None for an unknown key.
        """
        return self._previews.get(key)

    def save(self) -> None:
        """Write the decisions file: the decided photos, in the review's order."""
        write_decisions(self._source.target, self.decisions())

    def on_disk(self) -> UnwantedProof:
        """Read the decisions file back from the disk.

        Returns:
            What it holds, photo by photo.
        """
        return read_unwanted_back(self._source.target, self._keys)

    def decide(self, choices: Mapping[int, bool | None]) -> UnwantedProof:
        """Record choices, save them in one write, then read the file back.

        Args:
            choices: By photo rank: True sets it aside, False keeps it, None
                makes it undecided again.

        Returns:
            Those photos, as the file read back from the disk holds them.

        Raises:
            DecisionsError: An unknown photo, or a file that does not hold the
                choices once saved.
        """
        if any(not 0 <= rank < len(self._states) for rank in choices):
            raise DecisionsError(_("There is no such photo."))
        for rank, aside in choices.items():
            if aside is None:
                self._aside.pop(rank, None)
            else:
                self._aside[rank] = aside
        self.save()
        return unwanted_proven(self.on_disk(), choices)

    def decisions(self) -> DecisionsFile:
        """Build the decisions file: what it held, the decided photos in order.

        Returns:
            The decisions, in host paths.
        """
        keys = {rank: key for key, rank in self._keys.items()}
        photos = self._source.photos
        listed = tuple(
            photo_entry(keys[rank], photos[rank], aside=self._aside[rank])
            for rank in sorted(self._aside)
        )
        return self._base.model_copy(update={"unwanted": listed})
