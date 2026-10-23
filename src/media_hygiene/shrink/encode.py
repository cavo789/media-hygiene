"""Re-encode one video in H.264 with `ffmpeg`, keeping what the file knows.

The picture: x264 at the CRF of the level asked, 4:2:0 (what every player reads), turned
upright as it is shown, at most `lighter_lines` lines on its short side with
`--lighter`. The sound: every track, in AAC. The tags: the date (`creation_time`), the
local date and the place Apple writes, the place (`location`), copied as they are
(`-map_metadata 0`, `use_metadata_tags`). Written into an MP4 under a temporary name; a
time limit ten times the length of the film, at least `_LEAST_SECONDS`.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.scan.tool_run import run_tool
from media_hygiene.shrink.estimate import AUDIO_RATE

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.shrink_settings import ShrinkSettings

_BEFORE_INPUT: Final = ("-nostdin", "-v", "error")
_STREAMS: Final = ("-map", "0:v:0", "-map", "0:a?", "-map_metadata", "0")
_PICTURE: Final = ("-c:v", "libx264", "-pix_fmt", "yuv420p")
_SOUND: Final = ("-c:a", "aac", "-b:a", str(AUDIO_RATE))
_CONTAINER: Final = ("-movflags", "+faststart+use_metadata_tags", "-f", "mp4")
# The short side at most N lines, the other one even (`-2`), once turned upright.
_FIT: Final = (
    "scale='if(gt(iw,ih),-2,min(iw,{lines}))':'if(gt(iw,ih),min(ih,{lines}),-2)'"
)
_SLOWER_THAN_FILM: Final = 10
_LEAST_SECONDS: Final = 600


@dataclass(frozen=True, slots=True)
class Encoding:
    """How a video is re-encoded: its quality, size and speed."""

    crf: int
    lines: int | None  # at most this many lines on the short side, or the same size
    preset: str
    threads: int


def encoding_of(settings: ShrinkSettings, *, lighter: bool) -> Encoding:
    """Choose the encoding of a level.

    Args:
        settings: The `[shrink]` settings.
        lighter: `--lighter`: a stronger compression, at most `lighter_lines` lines.

    Returns:
        The encoding; `threads` 0 becomes half of the processors.
    """
    threads = settings.threads or max(1, (os.cpu_count() or 2) // 2)
    if lighter:
        return Encoding(
            settings.lighter_crf, settings.lighter_lines, settings.preset, threads
        )
    return Encoding(settings.same_crf, None, settings.preset, threads)


def ffmpeg_command(
    ffmpeg: str, files: tuple[Path, Path], encoding: Encoding
) -> tuple[str, ...]:
    """Write the command that re-encodes a video.

    Args:
        ffmpeg: The executable.
        files: The video, and the temporary file receiving the result.
        encoding: Quality, size and speed.

    Returns:
        The command.
    """
    source, target = files
    quality = ("-preset", encoding.preset, "-crf", str(encoding.crf))
    fit = () if encoding.lines is None else ("-vf", _FIT.format(lines=encoding.lines))
    threads = ("-threads", str(encoding.threads))
    return (
        ffmpeg,
        *_BEFORE_INPUT,
        "-i",
        str(source),
        *_STREAMS,
        *_PICTURE,
        *quality,
        *fit,
        *_SOUND,
        *threads,
        *_CONTAINER,
        str(target),
    )


def encode(command: tuple[str, ...], duration: float) -> str | None:
    """Run the encoding to its end.

    Args:
        command: The `ffmpeg` command (`ffmpeg_command`).
        duration: The length of the film, in seconds: it sets the time limit.

    Returns:
        None when it worked, else why not (the last line `ffmpeg` printed).
    """
    seconds = max(_LEAST_SECONDS, duration * _SLOWER_THAN_FILM)
    run = asyncio.run(run_tool(command, seconds))
    if run is None:
        return f"ffmpeg took more than {round(seconds)} s"
    if run.returncode == 0:
        return None
    lines = run.stderr.decode(errors="replace").strip().splitlines()
    return lines[-1] if lines else f"ffmpeg exit code {run.returncode}"
