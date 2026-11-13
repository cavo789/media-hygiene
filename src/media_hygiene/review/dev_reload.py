"""Developer only (0771): a page open in a tab reloads itself once a template changes.

`home_dev` sets `MEDIA_HYGIENE_DEV_RELOAD=1`. Every answer then carries the latest
change time of the package's templates, and the page (`presence.html.j2`) asks for it
each second and reloads when it moves. A `.py` change restarts the server and is
followed by the run id instead (0354). Without the variable, which the shipped image
never sets, nothing is sent and nothing is polled.
"""

from __future__ import annotations

import os
import time
from importlib.resources import files
from pathlib import Path
from typing import Final

ENV_VAR: Final = "MEDIA_HYGIENE_DEV_RELOAD"
TEMPLATES_HEADER: Final = "X-Media-Hygiene-Templates"
_TEMPLATE_GLOB: Final = "*.j2"
_KEEP_S: Final = 0.5  # one walk of the package serves the answers of that long
_seen: tuple[float, str] = (0.0, "")


def enabled() -> bool:
    """Tell whether the developer's reload is on.

    Returns:
        True when `MEDIA_HYGIENE_DEV_RELOAD` is `1`.
    """
    return os.environ.get(ENV_VAR) == "1"


def templates_tag() -> str:
    """The latest change time of the package's templates, as a tag.

    Returns:
        The tag, empty when the reload is off.
    """
    global _seen  # noqa: PLW0603  # pylint: disable=global-statement
    if not enabled():
        return ""
    now = time.monotonic()
    if now - _seen[0] > _KEEP_S:
        root = Path(str(files("media_hygiene")))
        latest = max(
            (path.stat().st_mtime_ns for path in root.rglob(_TEMPLATE_GLOB)), default=0
        )
        _seen = (now, str(latest))
    return _seen[1]
