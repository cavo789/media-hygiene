"""Prove a lighter video before it replaces its original: never keep a worse one.

The result must last as long (± `_SECONDS_APART`), hold as many sound tracks, say the
same date and place as the original, and its frames at 10 to 90 % of its length must
decode (`scan.keyframes`, the frames the near-duplicate search reads).
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.scan.keyframes import fingerprint
from media_hygiene.scan.tool_run import run_tool
from media_hygiene.scan.video_meta import PROBE_ENTRIES, video_metadata

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.scan.metadata import MediaMetadata

_PROBE: Final = ("-v", "error", "-show_entries", PROBE_ENTRIES, "-of", "json")
_PROBE_SECONDS: Final = 60
_SECONDS_APART: Final = 0.5
_AUDIO: Final = "audio"


@dataclass(frozen=True, slots=True)
class Tools:
    """The executables: `ffprobe` reads, `ffmpeg` decodes."""

    ffmpeg: str
    ffprobe: str


@dataclass(frozen=True, slots=True)
class Probed:
    """What a video says about itself, and its sound tracks."""

    metadata: MediaMetadata
    sounds: int


def flaw(files: tuple[Path, Path], tools: Tools) -> str | None:
    """Tell what the lighter video lost, if anything.

    Args:
        files: The original, and the lighter video.
        tools: `ffmpeg` and `ffprobe`.

    Returns:
        None when it keeps everything, else the translated reason.
    """
    original, result = files
    before = asyncio.run(_probe(original, tools.ffprobe))
    after = asyncio.run(_probe(result, tools.ffprobe))
    length = None if after is None else after.metadata.duration
    if before is None or after is None or length is None:
        return _("the lighter video cannot be read")
    old, new = before.metadata, after.metadata
    if old.duration is not None and abs(old.duration - length) > _SECONDS_APART:
        return _("the lighter video lasts {after} s, not {before} s").format(
            after=round(length, 1), before=round(old.duration, 1)
        )
    if before.sounds != after.sounds:
        return _("the lighter video lost a sound track")
    if old.recorded_at != new.recorded_at or old.located != new.located:
        return _("the lighter video lost its date or its place")
    decoded = asyncio.run(fingerprint(result, length, tools.ffmpeg))
    return None if decoded is not None else _("the lighter video does not decode")


def refuse(reason: str | None) -> None:
    """Refuse a lighter video that failed or lost something.

    Args:
        reason: Why (`encode`, `flaw`), or None when it is proven.

    Raises:
        ValueError: There is a reason.
    """
    if reason is not None:
        raise ValueError(reason)


async def _probe(path: Path, ffprobe: str) -> Probed | None:
    """Read what a video says about itself.

    Args:
        path: The video.
        ffprobe: The executable.

    Returns:
        Its metadata and sound tracks, or None when it cannot be read.
    """
    run = await run_tool((ffprobe, *_PROBE, str(path)), _PROBE_SECONDS)
    if run is None or run.returncode != 0:
        return None
    try:
        probe = json.loads(run.stdout or b"{}")
    except ValueError:
        return None
    streams = probe.get("streams") if isinstance(probe, dict) else None
    if not isinstance(streams, list) or not streams:
        return None
    sounds = sum(
        isinstance(stream, dict) and stream.get("codec_type") == _AUDIO
        for stream in streams
    )
    return Probed(video_metadata(probe), sounds)
