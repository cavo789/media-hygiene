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
# A name the page's script declares at its top level (two spaces in).
_DECLARED: Final = re.compile(
    r"^  (?:const|let|function|async function) (\w+)", re.MULTILINE
)


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
        tree_photos="/api/tree/",
        folder_path="/api/folder",
        aside_path="/api/aside",
        hint_path="/api/hint",
        photos_path="/api/place-photos",
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


def test_your_places_are_sorted_by_name_with_home_first() -> None:
    """TODO 0236: the page sorts a copy (the file's order is each place's key)."""
    page = _page()

    assert (
        'new Intl.Collator(document.documentElement.lang, { sensitivity: "base" })'
        in page
    )
    assert (
        "[...state.places].sort((first, second) =>"
        " Number(second.home) - Number(first.home)" in page
    )
    assert "collator.compare(first.name, second.name)" in page
    assert "for (const place of sorted)" in page


def test_the_folders_are_split_sorted_and_filtered_by_the_page() -> None:
    """TODO 0238: to place / placed, by name, a filter box; the rank is kept."""
    page = _page()

    assert page.index('id="foldersTodo"') < page.index('id="foldersPlaced"')
    assert 'id="folderFilter"' in page
    assert 'id="todoFold" class="fold sub" open' in page  # to place: open
    assert 'id="placedFold" class="fold sub">' in page  # placed: folded
    assert "folders.filter((folder) => folderMatches(folder, typed))" in page
    assert ".sort(byFolderName)" in page
    assert "folders.sort" not in page  # a copy is sorted: the index is the API's rank
    assert "folded(" in page
    assert 'normalize("NFD")' in page
    assert 'event.key === "Escape"' in page
    assert "const mark = !folder.found" in page


def test_a_place_named_like_a_town_gets_a_hint_and_the_page_says_what_places_are() -> (
    None
):
    """TODO 0239: the editor's hint, the mark in the list, the intro sentence."""
    page = _page()

    assert 'id="townHint"' in page
    assert "paths.hint" in page
    hint = str(_texts()["townHint"])
    assert "{town}" in hint
    assert "classify" in hint
    assert "if (place.town)" in page
    assert "the grandparents'" in page


def test_no_name_is_declared_twice_in_the_script() -> None:
    """A second `const plain` was a SyntaxError: the whole map page stopped (0242)."""
    [script] = [part for part in _page().split("<script>") if "const T = " in part]
    names = _DECLARED.findall(script)
    assert len(names) > 20
    assert sorted({name for name in names if names.count(name) > 1}) == []


def test_any_folder_of_the_index_is_listed_as_a_tree() -> None:
    """TODO 0242: a fourth fold, folded, filtered; a click on the map moves the pin."""
    page = _page()

    assert page.index('id="foldersFold"') < page.index('id="treeFold"')
    assert 'id="treeFold" class="fold">' in page  # folded
    assert 'id="treeFilter"' in page
    assert 'tree: "/api/tree/"' in page
    assert "if (node.count) button.addEventListener" in page  # none without GPS: grey
    assert "if (known) { showFolder(known.rank); return; }" in page
    assert "if (folderPin) folderPin.setLatLng(event.latlng);" in page
