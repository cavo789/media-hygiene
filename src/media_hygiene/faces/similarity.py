"""How alike two faces must be, without numpy: the settings read it at every start."""

from __future__ import annotations

from typing import Final

# SFace's documented cosine threshold for "same person".
SFACE_SIMILARITY: Final = 0.363
