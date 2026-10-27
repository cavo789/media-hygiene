"""The shared parts of a page of photos to pick, as each one shows in the page served.

`review/templates/pick_*` (skill photo-picking-pages): a page built from them holds each
part once — no copy of their code left behind.
"""

from __future__ import annotations

from typing import Final

PICK_PARTS: Final = (
    'id="keys"',  # pick_keys.html.j2
    '<span id="acting" hidden>',  # pick_acting.html.j2
    'id="viewerHelp"',  # pick_viewer.html.j2
    "function wireCard(node, index)",  # pick_grid.js.j2
    "const VIEWER_KEYS = {",  # pick_viewer.js.j2
    '$("grid").addEventListener("pointerdown"',  # pick_band.js.j2
)
