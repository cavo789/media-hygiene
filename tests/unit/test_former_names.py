"""The copies `clean` removed: the index rows and the words they give (TODO 0207)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.classify.former import FormerCopy
from media_hygiene.index.former_names import (
    forget_former,
    former_copies,
    former_of,
    remember_former,
)
from media_hygiene.index.parked import park, unpark
from media_hygiene.index.schema import prepare
from media_hygiene.tags.models import Tag, TagSource
from media_hygiene.tags.producers import cheap_tags, former_words
from tests.unit.test_tag_producers import context, photo

if TYPE_CHECKING:
    from collections.abc import Iterator

_KEPT: Final = "/data/c/Photos/DCIM/IMG_0001.jpg"
_WEDDING: Final = FormerCopy(
    Path("/data/d/Backup/Mariage Julie 2015/IMG_0001.jpg"), Path("/data/d/Backup")
)
_NAMED: Final = FormerCopy(
    Path("/data/d/Backup/2015/Gâteau Julie.jpg"), Path("/data/d/Backup")
)


@pytest.fixture(name="connection")
def fixture_connection() -> Iterator[sqlite3.Connection]:
    """An empty index in memory, closed after the test."""
    with closing(sqlite3.connect(":memory:")) as connection:
        prepare(connection)
        yield connection


def test_rows_are_kept_by_the_kept_file_and_read_back(
    connection: sqlite3.Connection,
) -> None:
    """Every copy is remembered once, in path order."""
    remember_former(connection, "run1", [(_KEPT, _WEDDING), (_KEPT, _NAMED)])
    remember_former(connection, "run1", [(_KEPT, _WEDDING)])
    assert former_of(connection, Path(_KEPT)) == (_NAMED, _WEDDING)
    assert former_copies(connection) == {Path(_KEPT): (_NAMED, _WEDDING)}


def test_undo_forgets_only_the_copies_of_its_run(
    connection: sqlite3.Connection,
) -> None:
    """A copy brought back by the undo of another run keeps its row."""
    remember_former(connection, "run1", [(_KEPT, _WEDDING)])
    remember_former(connection, "run2", [(_KEPT, _NAMED)])
    forget_former(connection, "run2", [str(_WEDDING.path), str(_NAMED.path)])
    assert former_of(connection, Path(_KEPT)) == (_WEDDING,)


def test_a_kept_file_set_aside_parks_its_rows_and_gets_them_back(
    connection: sqlite3.Connection,
) -> None:
    """A later clean setting the kept file aside parks them; its undo restores."""
    remember_former(connection, "run1", [(_KEPT, _WEDDING)])
    quarantined = "/quarantine/run2/c/Photos/DCIM/IMG_0001.jpg"
    park(connection, "run2", [(_KEPT, quarantined)])
    assert not former_copies(connection)
    unpark(connection, [(quarantined, _KEPT)])
    assert former_of(connection, Path(_KEPT)) == (_WEDDING,)


def test_an_index_read_only_and_older_has_none() -> None:
    """Without the table (an older index opened read-only), nothing is remembered."""
    with closing(sqlite3.connect(":memory:")) as older:
        assert former_copies(older) == {}


def test_former_words_are_those_of_the_removed_folders_and_names() -> None:
    """`Mariage Julie 2015` and `Gâteau Julie.jpg` give their words, once each."""
    file = replace(photo("DCIM/IMG_0001.jpg"), former=(_WEDDING, _NAMED))
    assert former_words(file, context()) == ("Mariage", "Julie", "Gâteau", "Julie")
    tags = [
        tag for tag in cheap_tags(file, context()) if tag.source is TagSource.FORMER
    ]
    assert tags == [
        Tag(TagSource.FORMER, "Mariage"),
        Tag(TagSource.FORMER, "Julie"),
        Tag(TagSource.FORMER, "Gâteau"),
    ]


def test_words_the_file_already_has_are_not_repeated() -> None:
    """A kept file in `Julie` does not get `Julie` again from its copies."""
    file = replace(photo("Julie/IMG_0001.jpg"), former=(_WEDDING,))
    assert former_words(file, context()) == ("Mariage",)


def test_a_file_without_removed_copies_has_no_former_word() -> None:
    """Nothing removed: no word."""
    assert not former_words(photo("DCIM/IMG_0001.jpg"), context())
