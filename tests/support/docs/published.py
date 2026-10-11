"""The commands the tool suggests, as a reader of the documentation would see them.

The demo runs on Docker volumes of its own, in a language given by `--locale`, without
colours: the `docker run` lines the tool prints name all of that. The documentation
shows them as on WSL instead: the photos under /mnt, the tool folders in the home.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from tests.support.docs.names import Locale

if TYPE_CHECKING:
    from tests.support.docs.container import Demo

_HOME: Final = "$HOME/media-hygiene"
_CACHE: Final = "media-hygiene-cache"  # the named volume the guides advise
_ALWAYS_GIVEN: Final = " --color never"


def _hosts(demo: Demo) -> dict[str, str]:
    """What stands for each volume of the demo in the documentation."""
    hosts = {
        "c": "/mnt/c/Photos",
        "d": f"/mnt/d/{demo.library.names.old_disk}",
        "cache": _CACHE,
    }
    for kind in ("config", "reports", "journal", "quarantine"):
        hosts[kind] = f"{_HOME}/{kind}"
    return hosts


def as_published(demo: Demo, text: str) -> str:
    """Rewrite the suggested commands of a capture for the documentation.

    Args:
        demo: The demo the capture comes from.
        text: The capture.

    Returns:
        The capture, its volumes named as a user's folders, without the options every
        documentation run adds (`--color never`, `--locale en`: English is the default).
    """
    for kind, host in _hosts(demo).items():
        text = re.sub(rf'"{re.escape(demo.volume(kind))}:', f'"{host}:', text)
    text = text.replace(_ALWAYS_GIVEN, "")
    if demo.locale == Locale.EN:
        text = text.replace(f" --locale {Locale.EN}", "")
    return text
