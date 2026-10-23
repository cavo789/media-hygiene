"""`shrink`: a lighter video that lost something is refused, saying what."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.scan.video_models import VideoPrint
from media_hygiene.shrink import check
from media_hygiene.shrink.check import Probed, Tools, flaw, refuse

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

_FILES = (Path("/v/clip.avi"), Path("/v/clip.mp4.media-hygiene.tmp"))
_TOOLS = Tools("ffmpeg", "ffprobe")
_DATED = MediaMetadata(duration=60.0, created="2015-07-14T10:00:00Z")


def _probes(
    before: Probed | None, after: Probed | None
) -> Callable[[Path, str], Coroutine[None, None, Probed | None]]:
    """A probe answering `before` for the original, `after` for the result."""

    async def probe(path: Path, _ffprobe: str) -> Probed | None:
        return before if path == _FILES[0] else after

    return probe


@pytest.fixture(autouse=True)
def decodes(monkeypatch: pytest.MonkeyPatch) -> None:
    """Frames decode, unless a test says otherwise."""

    async def frames(_path: Path, _duration: float, _ffmpeg: str) -> VideoPrint:
        return VideoPrint(())

    monkeypatch.setattr(check, "fingerprint", frames)


@pytest.mark.parametrize(
    ("after", "said"),
    [
        (None, "cannot be read"),
        (Probed(MediaMetadata(), 1), "cannot be read"),
        (Probed(_DATED.model_copy(update={"duration": 58.0}), 1), "lasts 58.0 s"),
        (Probed(_DATED, 0), "lost a sound track"),
        (Probed(_DATED.model_copy(update={"created": None}), 1), "date or its place"),
    ],
)
def test_each_loss_is_refused(
    monkeypatch: pytest.MonkeyPatch, after: Probed | None, said: str
) -> None:
    """Unreadable, shorter, silent, undated: a reason each."""
    monkeypatch.setattr(check, "_probe", _probes(Probed(_DATED, 1), after))
    reason = flaw(_FILES, _TOOLS)
    assert reason is not None
    assert said in reason


def test_kept_whole_then_frames_that_do_not_decode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Same length, sound, date: proven; until a frame does not decode."""
    monkeypatch.setattr(check, "_probe", _probes(Probed(_DATED, 1), Probed(_DATED, 1)))
    assert flaw(_FILES, _TOOLS) is None

    async def broken(_path: Path, _duration: float, _ffmpeg: str) -> None:
        return None

    monkeypatch.setattr(check, "fingerprint", broken)
    assert flaw(_FILES, _TOOLS) == "the lighter video does not decode"


def test_refuse_raises_only_with_a_reason() -> None:
    """None passes; a reason is a ValueError carrying it."""
    refuse(None)
    with pytest.raises(ValueError, match="lost"):
        refuse("lost")
