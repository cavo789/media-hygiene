"""The map page: what it hands Leaflet as tooltips is text, never HTML.

Leaflet writes a string tooltip with `innerHTML`; a place name (from `config.toml`,
partly from OpenStreetMap) must reach the page as text even if the name validator is
loosened.
"""

from __future__ import annotations

import re
from typing import Final

from media_hygiene.i18n.templates import translated_environment

_TOOLTIP: Final = re.compile(r"\.bindTooltip\(([^\n]*)")
_LABEL: Final = re.compile(
    r"const label = \(text\) => \{[^\n]*textContent = text; return span; \};"
)


def _page() -> str:
    """Render the map page as `serve_places` does."""
    environment = translated_environment("media_hygiene.places", escaped=("html", "j2"))
    return environment.get_template("places.html.j2").render(
        state_path="/api/state",
        save_path="/api/places",
        search_path="/api/search",
        osm_path="",
        osm_host="",
        tiles="https://tile.example/{z}/{x}/{y}.png",
        attribution="© example",
    )


def test_every_tooltip_is_a_text_node() -> None:
    """Each `bindTooltip` gets `label(…)`, a span filled through `textContent`."""
    page = _page()
    calls = _TOOLTIP.findall(page)
    assert len(calls) == 2  # the clusters and the saved places
    assert all(call.startswith("label(") for call in calls)
    assert _LABEL.search(page)


def test_no_place_name_is_written_as_html() -> None:
    """`innerHTML` is only read (to escape the attribution), never assigned."""
    assert not re.search(r"innerHTML\s*=", _page())
