"""Run inside a worker of the image pool: what did its fork server import?"""

from __future__ import annotations

import sys


def cli_loaded() -> bool:
    """Tell whether the worker holds any module of the command line.

    Returns:
        True when `media_hygiene.cli` or one of its modules is imported.
    """
    return any(name.startswith("media_hygiene.cli") for name in sys.modules)
