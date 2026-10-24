"""The lighter video of one job: a draft of `shrink --try` reused, or a new encoding.

A draft made from this very version of the original (same path, size, modification
time: `Recipe.drafts`) is moved beside it with `move_no_replace` (from the cache, on
another volume: a copy proven by its SHA-256), then proven again (`check.flaw`): never
encoded twice (0307). Any other job is encoded beside the original. A result that
fails is removed, the original untouched.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from media_hygiene.actions.no_overwrite import move_no_replace
from media_hygiene.shrink.check import flaw, refuse
from media_hygiene.shrink.encode import encode, ffmpeg_command

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.shrink import Recipe
    from media_hygiene.shrink.candidates import Candidate


def lighter_video(job: Candidate, temporary: Path, recipe: Recipe) -> int:
    """Write the lighter video under the temporary name and prove it.

    Args:
        job: The video.
        temporary: Where the result is written, beside the original.
        recipe: The encoding, the tools and the drafts already made.

    Returns:
        The size of the result.

    Raises:
        OSError: The draft could not be moved, or the result read.
        ValueError: The encoding failed or the result lost something (removed).
    """
    draft = recipe.drafts.get(job.key)
    try:
        if draft is not None:
            move_no_replace(draft, temporary)
            reason = None
        else:
            command = ffmpeg_command(
                recipe.tools.ffmpeg, (job.path, temporary), recipe.encoding
            )
            reason = encode(command, job.duration)
        refuse(reason or flaw((job.path, temporary), recipe.tools))
        return temporary.stat().st_size
    except OSError, ValueError:
        with contextlib.suppress(OSError):
            temporary.unlink()
        raise
