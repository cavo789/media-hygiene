"""The descriptions and mappings cached in the index."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.ai.models import Description
from media_hygiene.constants import MediaKind
from media_hygiene.index.descriptions import DescriptionStore, PhotoVersion
from media_hygiene.index.facts import FileFacts
from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan.models import MediaFile

if TYPE_CHECKING:
    from pathlib import Path

BEACH = Description("A beach.", ("sea",), 3.0)


def test_a_description_belongs_to_one_version_model_and_prompt(tmp_path: Path) -> None:
    """Reopened: still there; another mtime, model or prompt: unknown."""
    index, photo = tmp_path / "index.sqlite", PhotoVersion(tmp_path / "a.jpg", 10, 1)
    with FactsRepository.open(index) as repository:
        DescriptionStore(repository.connection, ("m", "p1")).put(photo, BEACH)
    with FactsRepository.open(index) as repository:
        store = DescriptionStore(repository.connection, ("m", "p1"))
        assert store.get(photo) == BEACH
        assert store.get(PhotoVersion(photo.path, 10, 2)) is None
        assert DescriptionStore(repository.connection, ("m", "p2")).get(photo) is None
        assert DescriptionStore(repository.connection, ("n", "p1")).get(photo) is None


def test_the_time_per_photo_is_the_median_of_this_model(tmp_path: Path) -> None:
    """None before the first description."""
    with FactsRepository.open(None) as repository:
        store = DescriptionStore(repository.connection, ("m", "p"))
        assert store.seconds_per_photo() is None
        for index, seconds in enumerate((1.0, 2.0, 9.0)):
            photo = PhotoVersion(tmp_path / f"{index}.jpg", 1, 1)
            store.put(photo, Description("x", (), seconds))
        assert store.seconds_per_photo() == 2.0


def test_mappings_are_remembered_by_key() -> None:
    """An empty category (none fits) is an answer too."""
    with FactsRepository.open(None) as repository:
        store = DescriptionStore(repository.connection, ("m", "p"))
        assert store.mapping("k") is None
        store.put_mapping("k", "")
        assert store.mapping("k") == ""


def test_descriptions_follow_moves_and_go_with_forgotten_files(tmp_path: Path) -> None:
    """`sort` moves a photo: its description moves; a file gone: so is it."""
    old, new = tmp_path / "a.jpg", tmp_path / "b.jpg"
    with FactsRepository.open(None) as repository:
        repository.put(MediaFile(old, 10, 1, MediaKind.IMAGE), FileFacts())
        store = DescriptionStore(repository.connection, ("m", "p"))
        store.put(PhotoVersion(old, 10, 1), BEACH)
        repository.move([(str(old), str(new))])
        assert store.get(PhotoVersion(new, 10, 1)) == BEACH
        assert repository.forget([str(new)]) == 1
        assert store.get(PhotoVersion(new, 10, 1)) is None
