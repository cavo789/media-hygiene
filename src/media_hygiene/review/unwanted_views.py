"""What the page of `review --junk` receives: the photos, their reason, the groups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _
from media_hygiene.plan.unwanted import UnwantedReason
from media_hygiene.review.near_views import folder_and_name
from media_hygiene.review.views import (
    ORIGINAL_LINK,
    PREVIEW_LINK,
    preview_key,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.plan.unwanted import UnwantedPhoto
    from media_hygiene.scan.models import VisualFacts

_FROZEN = ConfigDict(frozen=True, extra="forbid")
# Photos on one screen: a reason with thousands of photos is shown page by page.
GROUP_SIZE: Final = 40


class PhotoState(BaseModel):
    """One photo as the page shows it, and the choice so far."""

    model_config = _FROZEN

    reason: str  # an `UnwantedReason`
    name: str
    preview: str
    folder: str
    original: str
    details: str
    decision: str = ""  # empty: undecided; `aside` or `kept`


class GroupState(BaseModel):
    """Photos of one reason shown together: a reason, or a page of it."""

    model_config = _FROZEN

    reason: str
    title: str
    photos: tuple[int, ...]  # ranks in `UnwantedReviewState.photos`


class UnwantedReviewState(BaseModel):
    """Everything the page needs: `GET /api/state`."""

    model_config = _FROZEN

    decisions_file: str
    decisions_place: str
    photos: tuple[PhotoState, ...]
    groups: tuple[GroupState, ...]
    reasons: dict[str, str]  # the translated text of each reason


def reason_texts() -> dict[str, str]:
    """Say each reason in the user's language.

    Returns:
        The text, by reason.
    """
    return {
        UnwantedReason.SCREENSHOT: _("screenshot or document"),
        UnwantedReason.TINY: _("tiny image"),
        UnwantedReason.DARK: _("nearly black"),
        UnwantedReason.WHITE: _("nearly white"),
        UnwantedReason.BLURRY: _("among the blurriest of your photos"),
    }


def photo_groups(photos: Sequence[UnwantedPhoto]) -> tuple[GroupState, ...]:
    """Cut the photos into groups: one per reason, pages of `GROUP_SIZE` at most.

    Args:
        photos: The photos, grouped by reason already (`unwanted_photos`).

    Returns:
        The groups, in the order of the photos.
    """
    ranks: dict[UnwantedReason, list[int]] = {}
    for rank, photo in enumerate(photos):
        ranks.setdefault(photo.reason, []).append(rank)
    texts = reason_texts()
    groups: list[GroupState] = []
    for reason, members in ranks.items():
        for start in range(0, len(members), GROUP_SIZE):
            page = tuple(members[start : start + GROUP_SIZE])
            title = _("{reason}: {first} to {last} of {total}").format(
                reason=texts[reason],
                first=human_number(start + 1),
                last=human_number(start + len(page)),
                total=human_number(len(members)),
            )
            groups.append(GroupState(reason=reason, title=title, photos=page))
    return tuple(groups)


@dataclass(frozen=True, slots=True)
class UnwantedStateBuilder:
    """Describes the photos for the page, in host paths."""

    mapper: HostPathMapper
    visuals: Mapping[Path, VisualFacts]

    def photo(self, photo: UnwantedPhoto) -> PhotoState:
        """Describe one photo, undecided.

        Args:
            photo: The photo and its reason.

        Returns:
            Its state.
        """
        file = photo.file
        folder, name = folder_and_name(self.mapper.to_host(file.path))
        visual = self.visuals[file.path]
        size = f"{visual.width} \N{MULTIPLICATION SIGN} {visual.height}"
        key = preview_key(file)
        return PhotoState(
            name=name,
            folder=folder,
            details=" · ".join((size, human_size(file.size))),
            preview=f"{PREVIEW_LINK}{key}.jpg",
            original=f"{ORIGINAL_LINK}{key}{file.path.suffix.lower()}",
            reason=photo.reason,
        )
