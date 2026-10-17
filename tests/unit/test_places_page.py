"""The map page: what it hands Leaflet as tooltips is text, never HTML.

Leaflet writes a string tooltip with `innerHTML`; a place name (from `config.toml`,
partly from OpenStreetMap) must reach the page as text even if the name validator is
loosened.
"""

from __future__ import annotations

import json
import re
from typing import Final

from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.i18n.templates import translated_environment

_TOOLTIP: Final = re.compile(r"\.bindTooltip\(([^\n]*)")
_LABEL: Final = re.compile(
    r"const label = \(text\) => \{[^\n]*textContent = text; return span; \};"
)
_TEXTS: Final = re.compile(r"const T = (\{.*?\});\n")


def _page() -> str:
    """Render the map page as `serve_places` does."""
    environment = translated_environment("media_hygiene.places", escaped=("html", "j2"))
    return environment.get_template("places.html.j2").render(
        state_path="/api/state",
        save_path="/api/places",
        search_path="/api/search",
        cluster_path="/api/cluster/",
        folders_path="/api/folders",
        folder_photos="/api/folder/",
        folder_path="/api/folder",
        osm_path="",
        osm_host="",
        tiles="https://tile.example/{z}/{x}/{y}.png",
        attribution="© example",
    )


def test_every_tooltip_is_a_text_node() -> None:
    """Each `bindTooltip` gets `label(…)`, a span filled through `textContent`."""
    page = _page()
    calls = _TOOLTIP.findall(page)
    assert len(calls) == 3  # the clusters, the saved places, the folder pin
    assert all(call.startswith("label(") for call in calls)
    assert _LABEL.search(page)


def test_no_place_name_is_written_as_html() -> None:
    """`innerHTML` is only read (to escape the attribution), never assigned."""
    assert not re.search(r"innerHTML\s*=", _page())


def _texts() -> dict[str, object]:
    """The page's texts, as the script reads them, in French."""
    with using(Locale.FR):
        found = _TEXTS.search(_page())
    assert found is not None
    texts: dict[str, object] = json.loads(found.group(1))
    return texts


def test_every_count_has_its_french_plural_forms() -> None:
    """TODO 0232: "0 photos sur 1" was one `_()`; now each count is a `ngettext`."""
    texts = _texts()

    assert texts["photos"] == ["{n} photo", "{n} photos"]
    assert texts["videos"] == ["{n} vidéo", "{n} vidéos"]
    assert texts["firstPhotos"] == [
        "La première photo sur {count}",
        "Les {n} premières photos sur {count}",
    ]
    assert texts["firstVideos"] == [
        "La première vidéo sur {count}",
        "Les {n} premières vidéos sur {count}",
    ]
    assert texts["withoutGps"] == "{files} sans GPS"


def test_one_drawer_replaces_both_panels() -> None:
    """TODO 0233: the photos open over the map, never at the end of a list."""
    page = _page()

    assert page.count('id="drawer"') == 1
    assert 'id="photos"' not in page
    assert 'id="folderPanel"' not in page
    assert page.index('id="map"') < page.index('id="drawer"')
