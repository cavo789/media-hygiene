"""The move dialog's buttons stay outside its scrolling part (0549)."""

from __future__ import annotations

from pathlib import Path

import media_hygiene.search as search_package

_TEMPLATE = Path(search_package.__file__).parent / "templates" / "move_dialog.html.j2"


def test_menu_is_outside_the_scrolling_body() -> None:
    """Close and Move are never inside the part that scrolls."""
    text = _TEMPLATE.read_text(encoding="utf-8")
    body = text[text.index('<div class="moveBody">') :]
    body = body[: body.index("</div>")]
    assert "moveSources" in body
    assert "<menu>" not in body
    assert "<menu>" in text[text.index("</div>", text.index('class="moveBody"')) :]
    assert ".moveBody { flex: 1 1 auto; min-height: 0; overflow: hidden auto;" in text
