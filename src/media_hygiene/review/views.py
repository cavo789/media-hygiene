"""What the review page receives: the series, their shots, and the choices so far."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _
from media_hygiene.plan.burst_proposals import (
    ProposalLimits,
    ShotLook,
    is_obvious,
    propose,
)

if TYPE_CHECKING:
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.plan.burst_proposals import Proposal
    from media_hygiene.plan.keeper import KeepPolicy
    from media_hygiene.plan.similar_models import BurstSeries, SimilarFindings
    from media_hygiene.scan.models import MediaFile

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_PREVIEW_KEY_LENGTH: Final = 24
PREVIEW_PREFIX: Final = "/preview/"
ORIGINAL_PREFIX: Final = "/original/"


class ShotState(BaseModel):
    """One shot as the page shows it."""

    model_config = _FROZEN

    name: str
    folder: str
    details: str
    preview: str
    original: str  # the file itself, bytes untouched: proof the preview is faithful
    protected: bool
    best: bool
    share: float = 1.0  # its sharpness, as a share of the sharpest shot's
    proposed: bool = False  # proposed to be set aside, for `reason`
    reason: str = ""  # an `AsideReason`; for the page only, never in decisions.json
    like: int | None = None  # `identical`: rank of the sharper shot it repeats
    size: int = 0  # bytes, for the order "space freed, largest first"


class SeriesState(BaseModel):
    """One burst series: its shots in time order, the ranks set aside, if seen."""

    model_config = _FROZEN

    camera: str
    shots: tuple[ShotState, ...]
    taken: str = ""  # EXIF date of its first shot, sortable as text; empty: unknown
    discarded: tuple[int, ...] = ()
    reviewed: bool = False  # in the decisions file, kept whole or not
    obvious: bool = False  # nothing to judge: only the proposal's keepers are left


class ReviewState(BaseModel):
    """Everything the page needs: `GET /api/state`."""

    model_config = _FROZEN

    decisions_file: str
    decisions_place: str
    series: tuple[SeriesState, ...]


def preview_key(file: MediaFile) -> str:
    """Name the preview of a file: stable, and new as soon as the file changes.

    Args:
        file: The shot, as audited.

    Returns:
        A key, safe in a URL, that browsers may cache.
    """
    identity = f"{file.path}\0{file.size}\0{file.mtime_ns}"
    return hashlib.sha256(identity.encode()).hexdigest()[:_PREVIEW_KEY_LENGTH]


@dataclass(frozen=True, slots=True)
class StateBuilder:
    """Describes the shots of the audit for the page, in host paths."""

    mapper: HostPathMapper
    policy: KeepPolicy
    similar: SimilarFindings  # the series' shots' visual facts and exposures
    limits: ProposalLimits = field(default_factory=ProposalLimits)  # `[review]`

    def series(self, burst: BurstSeries) -> SeriesState:
        """Describe one series, no shot set aside yet, with what is proposed aside.

        Args:
            burst: The series.

        Returns:
            Its state.
        """
        first = self.similar.visuals.get(burst.shots[0].path)
        looks = tuple(self._look(file, burst) for file in burst.shots)
        known = tuple(filter(None, looks))
        proposals = propose(known, self.limits) if len(known) == len(looks) else {}
        top = max((look.sharpness for look in known), default=0.0)
        shots = []
        for rank, (file, look) in enumerate(zip(burst.shots, looks, strict=True)):
            shot = self._shot(file, file == burst.best)
            if look is not None and top:
                share = min(look.sharpness / top, 1.0)
                shot = shot.model_copy(update=_proposed(share, proposals.get(rank)))
            shots.append(shot)
        return SeriesState(
            camera=(first.camera if first else None) or "",
            taken=(first.taken_at if first else None) or "",
            shots=tuple(shots),
            obvious=is_obvious(known, proposals),
        )

    def _look(self, file: MediaFile, burst: BurstSeries) -> ShotLook | None:
        """Gather what the proposals compare: sharpness, hash, exposure.

        Args:
            file: The shot.
            burst: Its series.

        Returns:
            Its look, or None when it was never measured.
        """
        visual = self.similar.visuals.get(file.path)
        if visual is None:
            return None
        return ShotLook(
            sharpness=visual.sharpness,
            phash=visual.phash,
            exposure=self.similar.exposures.get(file.path),
            keep=file == burst.best or self.policy.is_protected(file),
        )

    def _shot(self, file: MediaFile, best: bool) -> ShotState:  # noqa: FBT001
        """Describe one shot: name, folder, and what tells it from the others.

        Args:
            file: The shot.
            best: It is the sharpest of its series.

        Returns:
            Its state.
        """
        host = self.mapper.to_host(file.path)
        folder, name = host.rsplit("\\" if "\\" in host else "/", 1)
        visual = self.similar.visuals.get(file.path)
        details = [human_size(file.size)]
        if visual is not None:
            details.insert(0, f"{visual.width} \N{MULTIPLICATION SIGN} {visual.height}")
            details.append(
                _("sharpness {value}").format(value=human_number(visual.sharpness))
            )
            details.extend(filter(None, (visual.taken_at,)))
        return ShotState(
            name=name,
            folder=folder,
            details=" · ".join(details),
            preview=f"{PREVIEW_PREFIX}{preview_key(file)}.jpg",
            original=f"{ORIGINAL_PREFIX}{preview_key(file)}{file.path.suffix.lower()}",
            protected=self.policy.is_protected(file),
            best=best,
            size=file.size,
        )


def _proposed(share: float, proposal: Proposal | None) -> dict[str, object]:
    """Describe a shot's sharpness share and what is proposed for it.

    Args:
        share: Its sharpness, as a share of the sharpest shot's.
        proposal: Proposed aside, and why; None: kept.

    Returns:
        The fields of its state.
    """
    if proposal is None:
        return {"share": share}
    return {
        "share": share,
        "proposed": True,
        "reason": proposal.reason.value,
        "like": proposal.like,
    }
