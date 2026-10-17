"""Ask `ffprobe` whether a video can be opened, and what it says about itself."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.scan.read_errors import is_read_error_message
from media_hygiene.scan.tool_run import run_tool
from media_hygiene.scan.video_meta import PROBE_ENTRIES, video_metadata

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.scan.metadata import MediaMetadata

_LOGGER = logging.getLogger(__name__)
_TIMEOUT_SECONDS: Final = 60
_PROBE_ARGS: Final = ("-v", "error", "-show_entries", PROBE_ENTRIES, "-of", "json")


@dataclass(frozen=True, slots=True)
class VideoProbe:
    """Outcome of probing a video: the probe error, or what the video holds.

    `unread`: the problem is a failed read (`read_errors`), not a damaged file.
    """

    problem: str | None = None
    metadata: MediaMetadata | None = None
    unread: bool = False


async def probe_video(path: Path, ffprobe: str) -> VideoProbe:
    """Probe a video: a container ffprobe cannot open, or without any stream, is broken.

    A probe that times out is inconclusive: the file is then considered healthy. A
    probe whose last line is the system message of a failed read (`Input/output
    error`…) tells nothing of the file: it is `unread`, not broken.

    Args:
        path: Video file.
        ffprobe: Path of the `ffprobe` executable.

    Returns:
        The probe error, or the metadata of a video that looks readable.
    """
    run = await run_tool((ffprobe, *_PROBE_ARGS, str(path)), _TIMEOUT_SECONDS)
    if run is None:
        _LOGGER.warning("ffprobe timed out on %s: kept as healthy", path)
        return VideoProbe()
    if run.returncode != 0:
        lines = run.stderr.decode(errors="replace").strip().splitlines()
        if not lines:
            return VideoProbe(f"ffprobe exit code {run.returncode}")
        return VideoProbe(lines[-1], unread=is_read_error_message(lines[-1]))
    try:
        probe = json.loads(run.stdout or b"{}")
    except ValueError:
        probe = {}
    if not isinstance(probe, dict) or not probe.get("streams"):
        return VideoProbe("no audio or video stream")
    return VideoProbe(metadata=video_metadata(probe))
