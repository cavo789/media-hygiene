"""A useless tag dropped from the search page (0546): everywhere, and restored."""

from __future__ import annotations

import json
import tomllib
from typing import TYPE_CHECKING, Final

from media_hygiene.config.tags_settings import STOP_WORDS
from media_hygiene.tags.stop_edit import add_stop_word, dropped_words, remove_stop_word
from media_hygiene.tags.xmp_doc import items, parse
from media_hygiene.tags.xmp_merge import (
    SUBJECT,
    XmpValues,
    new_document,
    take_back_subject,
)
from tests.support.cli import run
from tests.support.search_page import serve_search

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

_HAND: Final = "POST /api/hand-tag"


def test_dropped_everywhere_never_back_then_restored(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Seen first; off the index and the sidecar; not back; restored by `tags`."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    first = serve_search(
        cli, monkeypatch, [(_HAND, {"action": "drop_look", "word": "Durbuy"})]
    )
    look = json.loads(first[0].body)
    assert look["count"] == 3
    assert len(look["thumbs"]) == 3
    source = next(
        p
        for p in locations.data_dir.rglob("*")
        if "durbuy" in str(p).lower() and p.is_file()
    )
    sidecar = source.with_name(source.name + ".xmp")
    sidecar.write_bytes(new_document(XmpValues(("Durbuy", "ours")), "test").to_bytes())
    dropped = serve_search(
        cli,
        monkeypatch,
        [
            (_HAND, {"action": "drop", "word": "Durbuy"}),
            (_HAND, {"action": "drop_look", "word": "Durbuy"}),
        ],
    )
    answer = json.loads(dropped[0].body)
    assert answer["dropped"] == ["Durbuy"]
    assert "still on 0 photos" in answer["saved"]
    assert json.loads(dropped[1].body)["count"] == 0
    assert items(parse(sidecar.read_bytes()).find(SUBJECT)) == ["ours"]
    written = tomllib.loads(locations.config_file.read_text("utf-8"))
    assert "Durbuy" in written["tags"]["stop_words"]
    assert set(STOP_WORDS) <= set(written["tags"]["stop_words"])

    assert run(cli, "tags", "--no-describe").exit_code == 0
    again = serve_search(
        cli, monkeypatch, [(_HAND, {"action": "drop_look", "word": "durbuy"})]
    )
    assert json.loads(again[0].body)["count"] == 0

    back = serve_search(
        cli,
        monkeypatch,
        [
            (_HAND, {"action": "dropped"}),
            (_HAND, {"action": "restore", "word": "Durbuy"}),
        ],
    )
    assert json.loads(back[0].body)["dropped"] == ["Durbuy"]
    assert json.loads(back[1].body)["dropped"] == []
    assert run(cli, "tags", "--no-describe").exit_code == 0
    last = serve_search(
        cli, monkeypatch, [(_HAND, {"action": "drop_look", "word": "durbuy"})]
    )
    assert json.loads(last[0].body)["count"] == 3


def test_a_drop_without_a_word_is_refused(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing to drop: 400."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    answer = serve_search(cli, monkeypatch, [(_HAND, {"action": "drop", "word": " "})])
    assert answer[0].status == 400


def test_the_stop_words_keep_the_comments_and_the_built_in_list(tmp_path: Path) -> None:
    """The first word writes the whole list; back to built-in, the key goes."""
    config = tmp_path / "config.toml"
    config.write_text('# mine\n[tags]\nlanguage = "fr"\n', "utf-8")
    add_stop_word(config, "panneau de signalisation")
    add_stop_word(config, "PANNEAU DE SIGNALISATION")
    assert dropped_words(config) == ("panneau de signalisation",)
    assert "# mine" in config.read_text("utf-8")
    remove_stop_word(config, "Panneau de signalisation")
    assert not dropped_words(config)
    assert "stop_words" not in tomllib.loads(config.read_text("utf-8"))["tags"]


def test_what_another_application_wrote_stays_in_the_sidecar() -> None:
    """A word not in our memory is not ours to take back."""
    doc = new_document(XmpValues(("ours",)), "test")
    assert not take_back_subject(doc, "theirs")
    assert take_back_subject(doc, "OURS")
    assert items(doc.find(SUBJECT)) == []
