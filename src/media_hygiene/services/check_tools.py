"""What the integrity checks run with: the pool, `ffprobe`, `ffmpeg`, the read limit."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

from media_hygiene.constants import FFMPEG_BINARY, FFPROBE_BINARY
from media_hygiene.i18n import _
from media_hygiene.scan.deps import IntegrityTools

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.services.runtime import Runtime


def audit_tools(runtime: Runtime, executor: Executor) -> IntegrityTools:
    """Find `ffprobe` and `ffmpeg`, and say what is not done without them.

    Args:
        runtime: Settings (`[scan] read_whole_mb`) and output.
        executor: The pool decoding pictures.

    Returns:
        The tools, a missing program as None.
    """
    output = runtime.output
    ffprobe = shutil.which(FFPROBE_BINARY)
    if ffprobe is None:
        output.warning(_("ffprobe not found: videos are not checked."))
    ffmpeg = shutil.which(FFMPEG_BINARY)
    if ffmpeg is None:
        output.warning(
            _("ffmpeg not found: re-encoded copies of videos are not looked for.")
        )
    limit = runtime.settings.scan.read_whole_bytes
    return IntegrityTools(executor, ffprobe, ffmpeg, limit)


def check_tools(runtime: Runtime, executor: Executor) -> IntegrityTools:
    """The tools of a check that needs no `ffmpeg` and warns of nothing (`classify`).

    Args:
        runtime: Settings (`[scan] read_whole_mb`).
        executor: The pool decoding pictures.

    Returns:
        The pool, `ffprobe` when found, the read limit.
    """
    limit = runtime.settings.scan.read_whole_bytes
    return IntegrityTools(executor, shutil.which(FFPROBE_BINARY), read_limit=limit)
