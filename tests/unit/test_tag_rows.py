"""The tags of the index: replaced per source, read per version, forgotten, moved."""

from __future__ import annotations

from pathlib import Path

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.facts import FileFacts
from media_hygiene.index.listing import IndexedFile
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.tag_rows import TagStore, tags_reader
from media_hygiene.tags.models import FileTags, Tag, TagSource

PHOTO = PhotoVersion(Path("/data/c/a.jpg"), 10, 1)
FOLDER = Tag(TagSource.FOLDER, "Durbuy")
DATE = Tag(TagSource.DATE, "2019")
CAPTION = Tag(TagSource.CAPTION, "Un ours brun.", "vision")
BEAR = Tag(TagSource.VISION, "ours", "vision")


def test_a_source_is_replaced_whole_and_others_kept() -> None:
    """Rewriting the folder words drops the old ones, never the date."""
    with FactsRepository.open(None) as repository:
        store = TagStore(repository.connection)
        assert (
            store.replace(
                [TagSource.FOLDER, TagSource.DATE], [FileTags(PHOTO, (FOLDER, DATE))]
            )
            == 2
        )
        store.replace([TagSource.FOLDER], [FileTags(PHOTO, ())])
        assert store.of(PHOTO) == (DATE,)
        assert store.counts() == {TagSource.DATE: 1}


def test_a_changed_file_has_no_tags() -> None:
    """Another size or mtime: the rows of the old version are not read."""
    with FactsRepository.open(None) as repository:
        store = TagStore(repository.connection)
        store.replace([TagSource.FOLDER], [FileTags(PHOTO, (FOLDER,))])
        assert not store.of(PhotoVersion(PHOTO.path, 11, 1))


def test_forgotten_and_moved_files_take_their_tags() -> None:
    """`forget` drops them; `move` (sort, undo) carries them."""
    with FactsRepository.open(None) as repository:
        store = TagStore(repository.connection)
        store.replace([TagSource.FOLDER], [FileTags(PHOTO, (FOLDER,))])
        moved = Path("/data/c/2019/a.jpg")
        repository.move([(str(PHOTO.path), str(moved))])
        assert store.of(PhotoVersion(moved, 10, 1)) == (FOLDER,)
        repository.forget([str(moved)])
        assert store.counts() == {}


def test_the_inventory_cell_joins_words_without_the_sentence() -> None:
    """`Durbuy; ours`: the caption is for the search; None without tags."""
    with FactsRepository.open(None) as repository:
        store = TagStore(repository.connection)
        tags = (FOLDER, CAPTION, BEAR, Tag(TagSource.DATE, "Durbuy"))
        store.replace(list(TagSource), [FileTags(PHOTO, tags)])
        read = tags_reader(repository.connection)
        file = IndexedFile(PHOTO.path, 10, 1, FileFacts())
        assert read(file) == "Durbuy; ours"
        assert read(IndexedFile(Path("/data/c/b.jpg"), 1, 1, FileFacts())) is None
