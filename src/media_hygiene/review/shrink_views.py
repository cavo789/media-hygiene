"""What the page of `shrink --try` shows: each draft as it stands, and the file (0307).

The choices shown are those `shrink-decisions.json` holds, read from the disk at each
state: never a choice remembered in memory only.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.shrink.draft_bench import INSTANTS, DraftState
from media_hygiene.shrink.try_choices import read_choices

if TYPE_CHECKING:
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.services.shrink_try import Trial
    from media_hygiene.shrink.draft_bench import Draft

DRAFT_PREFIX: Final = "/draft/"
FRAME_PREFIX: Final = "/frame/"
_PERCENT: Final = 100
_CLOCK: Final = "%H:%M:%S"
_BUSY: Final = frozenset({DraftState.WAITING, DraftState.ENCODING})


class FrameView(BaseModel):
    """One instant: the original's frame (A) and the draft's (B)."""

    model_config = ConfigDict(frozen=True)

    at: float  # seconds into the film
    before: str
    after: str


class DraftView(BaseModel):
    """One video of the try, as the page draws it."""

    model_config = ConfigDict(frozen=True)

    number: int
    name: str
    folder: str  # as the Explorer shows it
    codec: str
    duration: float
    picture: str  # `1280x720`
    before: int  # bytes of the original
    estimated: int
    state: DraftState
    after: int = 0  # bytes of the draft, once ready
    gain: int = 0  # percent saved, once ready
    seconds: float = 0.0
    reason: str = ""
    video: str = ""  # where the page plays the draft
    frames: tuple[FrameView, ...] = ()
    chosen: bool = False


class FileView(BaseModel):
    """The decisions file, as read from the disk just now."""

    model_config = ConfigDict(frozen=True)

    path: str
    chosen: tuple[int, ...]  # the drafts' numbers
    read_at: str


class TryState(BaseModel):
    """Everything the page shows."""

    model_config = ConfigDict(frozen=True)

    drafts: tuple[DraftView, ...]
    busy: bool  # a draft is still waiting or encoding
    lighter: bool
    file: FileView | None = None


def try_state(trial: Trial, mapper: HostPathMapper) -> TryState:
    """Describe the try now, the choices read from the disk.

    Args:
        trial: The try.
        mapper: Turns container paths into the host's.

    Returns:
        The state.
    """
    choices = read_choices(trial.choices)
    file = None
    if choices is not None and choices.run == trial.run:
        numbers = tuple(choice.draft for choice in choices.chosen)
        file = FileView(
            path=str(trial.choices), chosen=numbers, read_at=time.strftime(_CLOCK)
        )
    picked = frozenset(file.chosen if file is not None else ())
    drafts = trial.bench.drafts()
    views = tuple(_view(draft, mapper, picked) for draft in drafts)
    busy = any(draft.state in _BUSY for draft in drafts)
    return TryState(drafts=views, busy=busy, lighter=trial.lighter, file=file)


def _view(draft: Draft, mapper: HostPathMapper, picked: frozenset[int]) -> DraftView:
    """Describe one draft.

    Args:
        draft: It.
        mapper: Turns container paths into the host's.
        picked: The drafts the file holds.

    Returns:
        Its view; the sizes, the video and the frames once ready.
    """
    video = draft.video
    look = video.look
    view = DraftView(
        number=draft.number,
        name=video.path.name,
        folder=mapper.to_host(video.path.parent),
        codec=video.codec,
        duration=look.duration,
        picture=f"{look.width}x{look.height}",
        before=video.size,
        estimated=video.estimated,
        state=draft.state,
        seconds=round(draft.seconds, 1),
        reason=draft.reason,
        chosen=draft.number in picked,
    )
    if draft.state is not DraftState.READY:
        return view
    number = draft.number
    frames = tuple(
        FrameView(
            at=round(look.duration * share, 1),
            before=f"{FRAME_PREFIX}{number}-a-{index}.jpg",
            after=f"{FRAME_PREFIX}{number}-b-{index}.jpg",
        )
        for index, share in enumerate(INSTANTS)
    )
    gain = round(_PERCENT * (video.size - draft.size) / video.size) if video.size else 0
    return view.model_copy(
        update={
            "after": draft.size,
            "gain": gain,
            "video": f"{DRAFT_PREFIX}{number}.mp4",
            "frames": frames,
        }
    )
