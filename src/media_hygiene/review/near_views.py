"""What the page of `review --near` receives: each group, its versions, the choices."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from media_hygiene.console.formatting import human_duration, human_size
from media_hygiene.report.near_reasons import level_text, near_why
from media_hygiene.review.videos import video_path
from media_hygiene.review.views import ORIGINAL_PREFIX, PREVIEW_PREFIX, preview_key

if TYPE_CHECKING:
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.plan.keeper import KeepPolicy
    from media_hygiene.plan.similar_models import NearDecision, SimilarFindings
    from media_hygiene.scan.models import MediaFile

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_PAIR_ARROW = " → "


class VersionState(BaseModel):
    """One version of a group as the page shows it."""

    model_config = _FROZEN

    original: str
    preview: str  # empty for a video: no preview, the original only
    video: str  # played in the page; empty for a picture or a format it cannot play
    name: str
    folder: str
    protected: bool
    details: str


class GroupState(BaseModel):
    """One group: the version the audit keeps, its copies, and the choice so far."""

    model_config = _FROZEN

    kept: VersionState
    copies: tuple[VersionState, ...]
    protected: tuple[VersionState, ...]
    why: str
    level: str
    sure: bool
    pair: str  # the kept version's folder → the first copy's: decided at once
    gain: int  # bytes freed by moving the copies as planned
    swappable: bool  # the kept version may go: it is not in a protected folder
    action: str = ""  # empty: undecided; else a `NearAction`


class NearReviewState(BaseModel):
    """Everything the page needs: `GET /api/state`."""

    model_config = _FROZEN

    decisions_file: str
    decisions_place: str
    groups: tuple[GroupState, ...]


def folder_and_name(host: str) -> tuple[str, str]:
    """Split a host path into its folder and its name.

    Args:
        host: A Windows or POSIX host path.

    Returns:
        The folder and the name.
    """
    folder, _sep, name = host.rpartition("\\" if "\\" in host else "/")
    return folder, name


@dataclass(frozen=True, slots=True)
class NearStateBuilder:
    """Describes the groups of the audit for the page, in host paths."""

    mapper: HostPathMapper
    policy: KeepPolicy
    similar: SimilarFindings

    def group(self, decision: NearDecision) -> GroupState:
        """Describe one group, undecided.

        Args:
            decision: The group, as the audit plans it.

        Returns:
            Its state.
        """
        kept = self.version(decision.keeper)
        copies = tuple(self.version(file) for file in decision.removable)
        return GroupState(
            kept=kept,
            copies=copies,
            protected=tuple(self.version(file) for file in decision.protected),
            why=near_why(decision, self._pixels),
            level=level_text(decision),
            sure=decision.sure is not None,
            pair=kept.folder + _PAIR_ARROW + copies[0].folder,
            gain=decision.reclaimable,
            swappable=not self.policy.is_protected(decision.keeper),
        )

    def version(self, file: MediaFile) -> VersionState:
        """Describe one version: name, folder, and what tells it from the others.

        Args:
            file: The version.

        Returns:
            Its state.
        """
        folder, name = folder_and_name(self.mapper.to_host(file.path))
        key = preview_key(file)
        visual = self.similar.visuals.get(file.path)
        look = self.similar.video_looks.get(file.path)
        details = [human_size(file.size)]
        if visual is not None:
            details.insert(0, f"{visual.width} \N{MULTIPLICATION SIGN} {visual.height}")
            details.extend(filter(None, (visual.taken_at,)))
        elif look is not None:
            details.insert(0, f"{look.width} \N{MULTIPLICATION SIGN} {look.height}")
            details.append(human_duration(look.duration))
            details.extend(filter(None, (look.codec, look.recorded_at)))
        return VersionState(
            name=name,
            folder=folder,
            details=" · ".join(details),
            preview=page_relative(f"{PREVIEW_PREFIX}{key}.jpg")
            if visual is not None
            else "",
            video=page_relative(video_path(key, file.path)) if look is not None else "",
            original=page_relative(f"{ORIGINAL_PREFIX}{key}{file.path.suffix.lower()}"),
            protected=self.policy.is_protected(file),
        )

    def _pixels(self, file: MediaFile) -> int:
        """The displayed resolution of a version, image or video.

        Args:
            file: The version.

        Returns:
            Its pixels.
        """
        visual = self.similar.visuals.get(file.path)
        if visual is not None:
            return visual.pixels
        return self.similar.video_looks[file.path].pixels


def page_relative(path: str) -> str:
    """An address relative to the page: the same at `/` or under a prefix (0357).

    Args:
        path: The address, from the root.

    Returns:
        It without its leading `/`; empty stays empty.
    """
    return path.removeprefix("/")
