"""A useless tag dropped from the search page (0546): everywhere, and restored."""

from __future__ import annotations

import json
import sqlite3
import tomllib
from typing import TYPE_CHECKING, Final

from media_hygiene.config.tags_settings import STOP_WORDS
from media_hygiene.constants import Locale
from media_hygiene.index.tag_merge import frequent, merge_word
from media_hygiene.tags.normalize import WordRules, normalize
from media_hygiene.tags.stop_edit import add_stop_word, dropped_words, remove_stop_word
from media_hygiene.tags.synonym_edit import (
    add_synonym,
    remove_synonym,
    saved_synonyms,
)
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
    assert not take_back_subject(doc, ("theirs",))
    assert take_back_subject(doc, ("OURS",))
    assert items(doc.find(SUBJECT)) == []


def test_several_tags_dropped_together_read_back(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Listed by frequency, seen and dropped together, in the stop words (0622)."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    listed = serve_search(cli, monkeypatch, [(_HAND, {"action": "frequent"})])
    tags = json.loads(listed[0].body)["frequent"]
    counts = [count for _, count in tags]
    assert counts == sorted(counts, reverse=True)
    words = [word for word, _ in tags[:2]]
    answers = serve_search(
        cli,
        monkeypatch,
        [
            (_HAND, {"action": "drop_look", "words": words}),
            (_HAND, {"action": "drop", "words": words}),
            (_HAND, {"action": "drop_look", "words": words}),
        ],
    )
    assert json.loads(answers[0].body)["count"] >= counts[0]
    assert set(words) <= set(json.loads(answers[1].body)["dropped"])
    assert json.loads(answers[2].body)["count"] == 0
    written = tomllib.loads(locations.config_file.read_text("utf-8"))
    assert set(words) <= set(written["tags"]["stop_words"])


def test_a_synonym_merged_follows_the_sidecar_and_survives_tags(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rows and sidecar take the tag; `tags` keeps it so; restored, it is back."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    source = next(
        p
        for p in locations.data_dir.rglob("*")
        if "durbuy" in str(p).lower() and p.is_file()
    )
    sidecar = source.with_name(source.name + ".xmp")
    sidecar.write_bytes(new_document(XmpValues(("Durbuy", "ours")), "test").to_bytes())
    merge = {"action": "merge", "word": "Durbuy", "target": "ardennes belges"}
    answers = serve_search(
        cli,
        monkeypatch,
        [
            (_HAND, merge),
            (_HAND, {"action": "drop_look", "word": "Durbuy"}),
            (_HAND, {"action": "drop_look", "word": "ardennes belges"}),
        ],
    )
    said = json.loads(answers[0].body)
    assert said["merged"] == [["Durbuy", "ardennes belges"]]
    assert "still on 0 photos" in said["saved"]
    assert json.loads(answers[1].body)["count"] == 0
    assert json.loads(answers[2].body)["count"] == 3
    assert items(parse(sidecar.read_bytes()).find(SUBJECT)) == [
        "ours",
        "ardennes belges",
    ]
    assert run(cli, "tags", "--no-describe").exit_code == 0
    kept = serve_search(
        cli, monkeypatch, [(_HAND, {"action": "drop_look", "word": "Durbuy"})]
    )
    assert json.loads(kept[0].body)["count"] == 0
    back = serve_search(
        cli, monkeypatch, [(_HAND, {"action": "restore", "word": "Durbuy"})]
    )
    assert json.loads(back[0].body)["merged"] == []
    assert run(cli, "tags", "--no-describe").exit_code == 0
    last = serve_search(
        cli, monkeypatch, [(_HAND, {"action": "drop_look", "word": "Durbuy"})]
    )
    assert json.loads(last[0].body)["count"] == 3


def test_a_merge_into_itself_or_nothing_is_refused(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing to name: 400."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    answers = serve_search(
        cli,
        monkeypatch,
        [
            (_HAND, {"action": "merge", "word": "Durbuy", "target": " "}),
            (_HAND, {"action": "merge", "word": "Durbuy", "target": "DURBUY"}),
        ],
    )
    assert [each.status for each in answers] == [400, 400]


def test_merging_rows_keeps_one_on_a_photo_with_both() -> None:
    """A photo with both tags keeps one row; only droppable sources change."""
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE tags (path TEXT, size INT, mtime_ns INT, source TEXT, value TEXT,"
        " PRIMARY KEY (path, source, value))"
    )
    rows = [
        ("a", 1, 1, "vision", "panneau"),
        ("a", 1, 1, "vision", "signal"),
        ("b", 1, 1, "vision", "panneau"),
        ("c", 1, 1, "hand", "panneau"),
    ]
    connection.executemany("INSERT INTO tags VALUES (?, ?, ?, ?, ?)", rows)
    assert frequent(connection, 1) == [("panneau", 2)]
    merge_word(connection, "PANNEAU", "signal")
    found = connection.execute("SELECT path, value FROM tags ORDER BY path").fetchall()
    connection.close()
    assert found == [("a", "signal"), ("b", "signal"), ("c", "panneau")]


def test_a_synonym_names_the_model_word_once(tmp_path: Path) -> None:
    """The next run's word; edited in config.toml, comments kept, removed."""
    rules = WordRules(Locale("fr"), frozenset(), (("panneau", "signal"),))
    assert normalize(("Panneaux", "signal", "chat"), rules) == ("signal", "chat")
    config = tmp_path / "config.toml"
    config.write_text("# mine\n", "utf-8")
    add_synonym(config, "panneau", "panneau de signalisation")
    assert saved_synonyms(config) == {"panneau": "panneau de signalisation"}
    assert "# mine" in config.read_text("utf-8")
    remove_synonym(config, "PANNEAU")
    assert not saved_synonyms(config)
