"""Words typed by hand on photos (TODO 0555): saved, read back, followed, searched.

Each word lives in `/config/tags/<word>.toml`, linked from `config.toml` with its
comments kept; the paths follow the tool's moves and the renames an audit finds; the
search page's desk gives a word to the photos picked and takes it off one.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import tomllib
from dataclasses import dataclass, field
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, cast

from media_hygiene.config.hand_tags import HandTag, linked_hand
from media_hygiene.config.photo_ref import PhotoRef, content_id
from media_hygiene.config.tags_settings import TagSettings
from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.search.hits import given_too
from media_hygiene.search.tag_cap import MOST_UNREAD
from media_hygiene.search.tag_desk import TagDesk
from media_hygiene.tags.hand_edit import (
    follow_hand_tags,
    give_word,
    hand_ids,
    relocate_hand_tags,
    take_word,
)
from media_hygiene.tags.hand_files import hand_words, read_hand_tags
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.search.hand_index import HandIndex

COMMENTED = "# my settings\n[tags]\n# my comment\nlanguage = ''\n"
A = PhotoRef(path="C:\\Photos\\a.jpg", id=f"{'a' * 16}:10")
B = PhotoRef(path="C:\\Photos\\b.jpg", id=f"{'b' * 16}:10")


def _config(tmp_path: Path) -> Path:
    """A `config.toml` with a comment of the user's."""
    config = tmp_path / "config.toml"
    config.write_text(COMMENTED, "utf-8")
    return config


def test_a_word_is_saved_in_its_file_linked_with_comments_kept(tmp_path: Path) -> None:
    """One file per word, linked; the same word in another case is one entry."""
    config = _config(tmp_path)
    give_word(config, HandTag(word="anniversaire Léa", photos=(A,)))
    give_word(config, HandTag(word="ANNIVERSAIRE léa", photos=(B, A)))
    text = config.read_text("utf-8")
    assert "# my comment" in text
    linked = tomllib.loads(text)["tags"]["hand"]
    assert linked == [
        {"word": "anniversaire Léa", "file": "tags/anniversaire Léa.toml"}
    ]
    assert (tmp_path / "tags" / "anniversaire Léa.toml").is_file()
    (entry,) = read_hand_tags(config)
    assert entry.photos == (A, B)  # each id once, the first spelling kept
    layer = linked_hand(tomllib.loads(text), tmp_path)
    assert TagSettings.model_validate(layer["tags"]).hand[0].photos == (A, B)


def test_a_word_taken_off_its_last_photo_goes_with_its_file(tmp_path: Path) -> None:
    """A word left on no photo leaves config.toml, its file deleted."""
    config = _config(tmp_path)
    give_word(config, HandTag(word="plage", photos=(A, B)))
    take_word(config, "Plage", {A.id})
    assert read_hand_tags(config)[0].photos == (B,)
    take_word(config, "plage", {B.id})
    assert not read_hand_tags(config)
    assert not (tmp_path / "tags" / "plage.toml").exists()
    assert "# my comment" in config.read_text("utf-8")


def test_paths_follow_the_moves_and_the_renames_found_by_id(tmp_path: Path) -> None:
    """The tool's moves and the renames an audit finds rewrite the paths."""
    config = _config(tmp_path)
    give_word(config, HandTag(word="plage", photos=(A, B)))
    moved = follow_hand_tags(config, {A.path: "C:\\Photos\\2019\\a.jpg"})
    assert moved == 1
    found = {B.id: ["D:\\Elsewhere\\b.jpg"]}
    assert relocate_hand_tags(config, found) == 1
    paths = [photo.path for photo in read_hand_tags(config)[0].photos]
    assert paths == ["C:\\Photos\\2019\\a.jpg", "D:\\Elsewhere\\b.jpg"]
    assert hand_ids(config) == {A.id, B.id}
    assert follow_hand_tags(config, {}) == 0


def test_the_search_shows_given_words_by_source() -> None:
    """Names and words typed by hand are replaced one source at a time."""
    path = Path("/data/c/a.jpg")
    given = given_too({}, TagSource.PERSON, {path: ("Léa",)})
    given = given_too(given, TagSource.HAND, {path: ("plage",)})
    assert given_too(given, TagSource.PERSON, {}) == {
        path: {TagSource.HAND: ("plage",)}
    }


@dataclass
class _Index:
    """The part of the search the desk uses: the files by key, their digests."""

    files: dict[int, PhotoVersion]
    connection: sqlite3.Connection = field(
        default_factory=lambda: sqlite3.connect(":memory:")
    )
    given: Mapping[Path, tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """One row per file, without digest: the desk reads the file."""
        self.connection.execute("CREATE TABLE files (full_digest TEXT)")
        for key in self.files:
            self.connection.execute("INSERT INTO files (rowid) VALUES (?)", (key,))

    def source_of(self, key: int) -> PhotoVersion | None:
        """The file of a key."""
        return self.files.get(key)

    def give_hand(self, words: Mapping[Path, tuple[str, ...]]) -> None:
        """Keep the words given, to check them."""
        self.given = words


def test_the_desk_gives_reads_back_and_takes_off(tmp_path: Path) -> None:
    """A word given to a key is read back, searched, then taken off."""
    data = tmp_path / "data"
    photo = data / "c" / "a.jpg"
    photo.parent.mkdir(parents=True)
    photo.write_bytes(b"0123456789")
    index = _Index({7: PhotoVersion(photo, 10, 1)})
    config = _config(tmp_path)
    desk = TagDesk(cast("HandIndex", index), HostPathMapper(data), config)
    body = json.dumps({"action": "add", "keys": [7], "word": " plage\n"}).encode()
    answer = desk.answer(body)
    assert answer.status is HTTPStatus.OK
    said = json.loads(answer.body)
    assert said["tags"] == {"7": ["plage"]}
    assert said["words"] == ["plage"]
    sha = hashlib.sha256(b"0123456789").hexdigest()
    assert read_hand_tags(config)[0].photos[0].id == content_id(sha, 10)
    assert hand_words(config, HostPathMapper(data)) == {photo: ("plage",)}
    assert index.given == {photo: ("plage",)}
    body = json.dumps({"action": "remove", "keys": [7], "word": "plage"}).encode()
    assert json.loads(desk.answer(body).body)["tags"] == {"7": []}
    assert not read_hand_tags(config)
    index.connection.close()


def test_the_desk_refuses_without_config_or_word(tmp_path: Path) -> None:
    """No /config, no word, a bad body: refused; a list asks nothing."""
    index = _Index({})
    mapper = HostPathMapper(tmp_path)
    no_config = TagDesk(cast("HandIndex", index), mapper, None)
    add = json.dumps({"action": "add", "keys": [1], "word": "x"}).encode()
    assert no_config.answer(add).status is HTTPStatus.CONFLICT
    desk = TagDesk(cast("HandIndex", index), mapper, _config(tmp_path))
    empty = json.dumps({"action": "add", "keys": [1], "word": " "}).encode()
    assert desk.answer(empty).status is HTTPStatus.BAD_REQUEST
    assert desk.answer(b"{").status is HTTPStatus.BAD_REQUEST
    listed = json.loads(desk.answer(b"{}").body)
    assert listed == {"words": [], "tags": {}, "saved": ""}
    index.connection.close()


def _desk_of(tmp_path: Path, count: int) -> tuple[TagDesk, _Index, Path]:
    """A desk on `count` real photos the index has no digest for."""
    data = tmp_path / "data"
    data.mkdir()
    files = {}
    for key in range(1, count + 1):
        photo = data / f"{key}.jpg"
        photo.write_bytes(b"0123456789")
        files[key] = PhotoVersion(photo, 10, 1)
    index = _Index(files)
    config = _config(tmp_path)
    return (
        TagDesk(cast("HandIndex", index), HostPathMapper(data), config),
        index,
        config,
    )


def _given(keys: list[int]) -> bytes:
    """The body of a word given to these keys."""
    return json.dumps({"action": "add", "keys": keys, "word": "plage"}).encode()


def test_tagging_up_to_the_cap_of_unread_photos_saves(tmp_path: Path) -> None:
    """0571: exactly the cap is read and saved, a key unknown not counted."""
    desk, index, config = _desk_of(tmp_path, MOST_UNREAD)
    answer = desk.answer(_given([*index.files, 999_999]))
    assert answer.status is HTTPStatus.OK
    assert read_hand_tags(config)[0].word == "plage"
    index.connection.close()


def test_over_the_cap_nothing_is_written_and_the_line_says_how_many(
    tmp_path: Path,
) -> None:
    """0571: one more photo to read is refused before any read or write."""
    desk, index, config = _desk_of(tmp_path, MOST_UNREAD + 1)
    answer = desk.answer(_given(list(index.files)))
    assert answer.status is HTTPStatus.UNPROCESSABLE_ENTITY
    said = json.loads(answer.body)["error"]
    assert f"{MOST_UNREAD + 1} photos not analysed yet" in said
    assert config.read_text("utf-8") == COMMENTED
    assert not read_hand_tags(config)
    assert not index.given
    index.connection.close()


def test_photos_the_index_knows_do_not_count_towards_the_cap(tmp_path: Path) -> None:
    """0571: with their digest known, many photos are not read and are saved."""
    desk, index, config = _desk_of(tmp_path, MOST_UNREAD + 1)
    index.connection.execute("UPDATE files SET full_digest = printf('%016x', rowid)")
    assert desk.answer(_given(list(index.files))).status is HTTPStatus.OK
    assert len(read_hand_tags(config)[0].photos) == MOST_UNREAD + 1
    index.connection.close()


def test_taking_a_word_off_is_never_capped(tmp_path: Path) -> None:
    """0571: a word taken off reads no file: the cap does not apply."""
    desk, index, _config_file = _desk_of(tmp_path, MOST_UNREAD + 1)
    body = json.dumps(
        {"action": "remove", "keys": list(index.files), "word": "plage"}
    ).encode()
    assert desk.answer(body).status is HTTPStatus.OK
    index.connection.close()
