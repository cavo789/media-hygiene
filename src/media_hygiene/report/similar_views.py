"""Near duplicates and bursts in the report: pictures side by side, with details."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from media_hygiene.constants import Sizes
from media_hygiene.paths.file_uri import file_uri
from media_hygiene.report.near_reasons import near_why
from media_hygiene.report.thumbnails import thumbnail_name
from media_hygiene.report.video_views import VideoSection, video_section

if TYPE_CHECKING:
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.plan.similar_models import (
        BurstSeries,
        NearDecision,
        SimilarFindings,
    )
    from media_hygiene.scan.models import MediaFile


@dataclass(frozen=True, slots=True)
class ShotView:  # pylint: disable=too-many-instance-attributes
    """One picture: where it is, its preview, and what tells it from the others."""

    path: str
    thumbnail: str | None
    width: int
    height: int
    size: int
    sharpness: float
    taken_at: str | None
    uri: str | None = None  # opens the photo itself, when its host path is known


@dataclass(frozen=True, slots=True)
class NearView:
    """A near-duplicate group: the version kept, and its smaller or worse copies."""

    kept: ShotView
    copies: tuple[ShotView, ...]
    protected: tuple[ShotView, ...]
    why: str = ""  # why the kept version won (`near_reasons`)


@dataclass(frozen=True, slots=True)
class BurstView:
    """A burst series, in time order, with its sharpest shot."""

    camera: str
    shots: tuple[ShotView, ...]
    best: str


@dataclass(frozen=True, slots=True)
class SimilarSection:
    """What the report lists beyond exact duplicates, and how many bursts are left out.

    Every near duplicate is listed: `clean --tier near` moves them all, so the report
    shows them all before the question is asked.
    """

    near: tuple[NearView, ...] = ()
    bursts: tuple[BurstView, ...] = ()
    hidden_bursts: int = 0
    videos: VideoSection = field(default_factory=VideoSection)


def similar_files(similar: SimilarFindings) -> list[MediaFile]:
    """List the pictures the similar sections preview.

    Args:
        similar: Near duplicates and bursts.

    Returns:
        Every picture shown.
    """
    shown_bursts = similar.bursts[: Sizes.MAX_BURSTS_IN_REPORT]
    return [
        *(
            file
            for decision in similar.near
            for file in (decision.keeper, *decision.removable, *decision.protected)
        ),
        *(file for series in shown_bursts for file in series.shots),
    ]


@dataclass(frozen=True, slots=True)
class SimilarRenderer:
    """Turns near duplicates and bursts into views, in host paths."""

    mapper: HostPathMapper
    previews: frozenset[str]

    def section(self, similar: SimilarFindings) -> SimilarSection:
        """Describe the similar pictures shown in the report.

        Args:
            similar: Near duplicates, bursts and the visual facts of images.

        Returns:
            The section.
        """
        limit = Sizes.MAX_BURSTS_IN_REPORT
        return SimilarSection(
            near=tuple(self._near(decision, similar) for decision in similar.near),
            bursts=tuple(self._burst(s, similar) for s in similar.bursts[:limit]),
            hidden_bursts=max(0, len(similar.bursts) - limit),
            videos=video_section(similar, self.mapper),
        )

    def _near(self, decision: NearDecision, similar: SimilarFindings) -> NearView:
        return NearView(
            kept=self._shot(decision.keeper, similar),
            copies=tuple(self._shot(file, similar) for file in decision.removable),
            protected=tuple(self._shot(file, similar) for file in decision.protected),
            why=near_why(decision, lambda file: similar.visuals[file.path].pixels),
        )

    def _burst(self, series: BurstSeries, similar: SimilarFindings) -> BurstView:
        first = similar.visuals[series.shots[0].path]
        return BurstView(
            camera=first.camera or "",
            shots=tuple(self._shot(file, similar) for file in series.shots),
            best=self.mapper.to_host(series.best.path),
        )

    def _shot(self, file: MediaFile, similar: SimilarFindings) -> ShotView:
        visual = similar.visuals[file.path]
        name, path = thumbnail_name(file), self.mapper.to_host(file.path)
        return ShotView(
            path=path,
            thumbnail=name if name in self.previews else None,
            width=visual.width,
            height=visual.height,
            size=file.size,
            sharpness=visual.sharpness,
            taken_at=visual.taken_at,
            uri=file_uri(path),
        )
