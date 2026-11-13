"""A search aimed at an album (0501): the field filled, the filter, the way back."""

from __future__ import annotations

from pathlib import Path
from typing import Final

_SRC: Final = Path(__file__).resolve().parents[2] / "src" / "media_hygiene"


def _template(package: str, name: str) -> str:
    return (_SRC / package / "templates" / name).read_text("utf-8")


def test_the_album_field_is_filled_once_from_the_address_with_a_way_back() -> None:
    """`?album=` fills the field and shows ← the album; nothing remembers it."""
    field = _template("review", "album_bar.html.j2")
    assert 'window.mhView.get({ album: "text" }).album' in field
    assert '"/albums/edit?album=" + encodeURIComponent(aimed)' in field
    assert "localStorage" not in field


def test_the_search_sends_the_album_and_marks_its_tiles() -> None:
    """The body names the album and the filter; a file in it shows so on its tile."""
    script = _template("search", "search.js.j2")
    assert "album: albumAimed()" in script
    assert "hit.inAlbum" in script
    assert (
        'for (const id of ["text", "from", "to"]) if (opened[id])' in script
    )  # the period of *Add photos*
    page = _template("search", "search.html.j2")
    for value in ('value="in"', 'value="out"'):
        assert value in page.split('id="albumIn"')[1].split("</select>")[0]


def test_the_album_page_offers_add_photos_aimed_at_it() -> None:
    """Add photos: the search with the album and a period around its dates."""
    script = _template("share", "album_edit.js.j2")
    assert "new URLSearchParams({ album: NAME })" in script
    assert 'asked.set("from"' in script
    assert 'id="addPhotos"' in _template("share", "album_edit.html.j2")


def test_prepare_for_sending_adds_keep_gps_when_the_setting_is_on() -> None:
    """0747: the saved `[share] keep_gps` makes the command end with `--keep-gps`."""
    options = _template("review", "share_options.html.j2")
    assert "window.mhShareKeepGps = values.keep_gps;" in options
    album_bar = _template("review", "album_bar.html.j2")
    assert '(window.mhShareKeepGps ? " --keep-gps" : "")' in album_bar
