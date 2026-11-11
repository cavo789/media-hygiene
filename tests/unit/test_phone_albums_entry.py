"""The phone's home page: one "Albums (N)" entry and 3 shortcuts at most (0548)."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from media_hygiene.review.home_texts_family import family_texts

_SRC: Final = Path(__file__).resolve().parents[2] / "src" / "media_hygiene"


def _template(package: str, name: str) -> str:
    return (_SRC / package / "templates" / name).read_text("utf-8")


def test_the_home_page_shows_one_entry_and_three_shortcuts_at_most() -> None:
    """Never one button per album: the entry counts them, the recent ones are capped."""
    script = _template("review", "home_run.js.j2")
    drawn = script.split("function tvAlbums()")[1].split("function tvChoices()")[0]
    assert "const TV_RECENT = 3;" in script
    assert ".slice(0, TV_RECENT)" in drawn
    assert "names.map(" not in drawn  # no button per album any more
    assert "T.tvAll" in drawn
    assert "?tv=1" in drawn
    assert "name !== T.lastSent" in drawn  # "Last sent" is never a shortcut


def test_a_tap_on_the_albums_page_shows_the_album_on_the_tv() -> None:
    """Opened with `?tv=1` on a phone, a card leads to the home page's TV start."""
    script = _template("share", "album.js.j2")
    assert '"tv" in window.mhView.get({ tv: "text" })' in script
    assert "`${P.home}?tv=${encodeURIComponent(name)}`" in script
    assert 'window.mhView.get({ tv: "text" }).tv' in _template(
        "review", "home_run.js.j2"
    )


def test_the_albums_page_filters_by_name_and_sorts_by_last_used() -> None:
    """A filter box narrows the cards; a delete only takes the cards shown."""
    script = _template("share", "album.js.j2")
    assert 'id="albumFilter"' in script
    assert "ordered(view.albums)" in script
    assert ".card:not([hidden]) [data-tick]:checked" in script


def test_a_send_replaces_a_single_last_sent_album() -> None:
    """The send names "Last sent" and deletes the previous one first."""
    album_bar = _template("review", "album_bar.html.j2")
    assert '_("Last sent")' in album_bar
    assert "Sent {date}" not in album_bar
    assert 'action: "delete", names: [TEXTS.sendName]' in album_bar
    assert family_texts()["lastSent"] == "Last sent"
