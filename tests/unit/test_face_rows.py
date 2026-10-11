"""The faces kept in the index: per version and model, followed, forgotten, counted."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from media_hygiene.constants import MediaKind
from media_hygiene.errors import FaceModelError, MountError
from media_hygiene.faces.models import PhotoFaces
from media_hygiene.faces.weights import DETECTOR, EMBEDDER
from media_hygiene.faces.worker import FaceJob, OnnxRecipe, find_faces
from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.face_coverage import face_coverage
from media_hygiene.index.face_rows import FaceStore
from media_hygiene.index.facts import FileFacts
from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan.models import MediaFile
from media_hygiene.services import people_models as people
from media_hygiene.services.people_files import require_people_index
from tests.support.faces import FakeRecipe, coloured, face_of
from tests.support.runtime import make_runtime, output_of

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations

MODEL = "test-model"


def photo_faces(path: Path, mtime_ns: int = 1, count: int = 2) -> PhotoFaces:
    """A photo of 10 bytes holding `count` faces of person 0."""
    faces = tuple(face_of(0, (60, 60)) for _ in range(count))
    return PhotoFaces(path, 10, mtime_ns, faces, 0.5)


def test_faces_are_kept_per_version_followed_and_forgotten(tmp_path: Path) -> None:
    """A changed file reads as not analysed; a moved one keeps its faces."""
    index = tmp_path / "index.sqlite"
    path = tmp_path / "a.jpg"
    with FactsRepository.open(index) as repository:
        repository.put(MediaFile(path, 10, 1, MediaKind.IMAGE), FileFacts())
        store = FaceStore(repository.connection, MODEL)
        assert not store.scanned(PhotoVersion(path, 10, 1))
        store.put(photo_faces(path))
        store.put(photo_faces(path))  # analysed again: replaced, not doubled
        assert store.scanned(PhotoVersion(path, 10, 1))
        assert not store.scanned(PhotoVersion(path, 10, 2))
        assert not FaceStore(repository.connection, "other").scanned(
            PhotoVersion(path, 10, 1)
        )
        assert [face.number for face in store.faces()] == [0, 1]
        tally = store.tally()
        assert (tally.photos, tally.faces, tally.seconds_per_photo) == (1, 2, 0.5)
        moved = tmp_path / "b.jpg"
        repository.move([(str(path), str(moved))])
        assert {face.path for face in store.faces()} == {moved}
        repository.forget([str(moved)])
        assert not store.faces()
    assert face_coverage(index) is None  # no photo analysed any more


def test_faces_of_an_older_version_are_not_read(tmp_path: Path) -> None:
    """A file changed since its faces were found shows none until analysed again."""
    path = tmp_path / "a.jpg"
    with FactsRepository.open(None) as repository:
        repository.put(MediaFile(path, 10, 2, MediaKind.IMAGE), FileFacts())
        store = FaceStore(repository.connection, MODEL)
        store.put(photo_faces(path, mtime_ns=1))
        assert not store.faces()
        assert store.forget() == (2, 0)


def test_face_coverage_counts_any_model(tmp_path: Path) -> None:
    """`status` counts photos and faces; without an index, or a foreign file, None."""
    index = tmp_path / "index.sqlite"
    assert face_coverage(None) is None
    assert face_coverage(index) is None
    with FactsRepository.open(index) as repository:
        FaceStore(repository.connection, MODEL).put(photo_faces(tmp_path / "a.jpg"))
        FaceStore(repository.connection, "x").put(photo_faces(tmp_path / "b.jpg", 1, 0))
    assert face_coverage(index) == (2, 2)
    foreign = tmp_path / "foreign.sqlite"
    foreign.write_bytes(b"not a database at all, really not")
    assert face_coverage(foreign) is None


def test_the_worker_finds_faces_and_skips_what_it_cannot_decode(tmp_path: Path) -> None:
    """A picture gives its faces and time; a damaged one gives None."""
    picture = coloured(tmp_path / "a.png", 2)
    found = find_faces(FaceJob(picture, 1, 1, FakeRecipe()))
    assert found is not None
    assert found.faces == (face_of(2, (96, 64)),)
    damaged = tmp_path / "b.jpg"
    damaged.write_bytes(b"\xff\xd8 not a jpeg")
    assert find_faces(FaceJob(damaged, 1, 1, FakeRecipe())) is None


def test_the_onnx_recipe_needs_the_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without the ONNX runtime, building the finder says so."""
    monkeypatch.setitem(sys.modules, "onnxruntime", None)
    with pytest.raises(FaceModelError):
        OnnxRecipe(tmp_path / "a.onnx", tmp_path / "b.onnx").build()


def test_the_recipe_downloads_once_and_says_so(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The first run says it downloads the models into the cache; later runs do not."""
    runtime = make_runtime(locations)
    monkeypatch.setattr(
        people, "ensure_model", lambda folder, model: folder / model.name
    )
    recipe = people.face_recipe(runtime)
    assert isinstance(recipe, OnnxRecipe)
    assert recipe.detector.parent == locations.cache_dir / "models"
    assert "Downloading the two face models" in output_of(runtime)
    for model in (DETECTOR, EMBEDDER):
        recipe.detector.parent.mkdir(exist_ok=True)
        (recipe.detector.parent / model.name).write_bytes(b"x")
    quiet = make_runtime(locations)
    people.face_recipe(quiet)
    assert "Downloading" not in output_of(quiet)


def test_people_needs_an_index(locations: Locations) -> None:
    """No index yet: audit first."""
    with pytest.raises(MountError, match="no photo to look at yet"):
        require_people_index(make_runtime(locations))
