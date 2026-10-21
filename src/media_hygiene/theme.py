"""The look every page of the tool shares, read once from `assets/` (0273).

The tokens (`assets/theme/tokens.css`) are written once; the served pages include them
after their `@font-face` rules, the reports (self-contained files, opened from disk)
inline them and keep the system fonts. The avatar is inlined too: a file cannot ask a
server for it.
"""

from __future__ import annotations

import base64
from functools import cache
from pathlib import Path
from typing import Final

from markupsafe import Markup

ASSETS_DIR: Final = Path(__file__).resolve().parent / "assets"
_TOKENS: Final = ASSETS_DIR / "theme" / "tokens.css"
_AVATAR: Final = ASSETS_DIR / "images" / "avatar.webp"


@cache
def theme_tokens() -> Markup:
    """The shared tokens, light and dark, and the page bar's rules.

    Returns:
        The CSS, safe to put in a `<style>` (it is the tool's own file).
    """
    return Markup(_TOKENS.read_text(encoding="utf-8"))  # noqa: S704


@cache
def avatar_data_uri() -> str:
    """The avatar as a `data:` address, for a page that cannot load files.

    Returns:
        The address.
    """
    encoded = base64.b64encode(_AVATAR.read_bytes()).decode("ascii")
    return f"data:image/webp;base64,{encoded}"
