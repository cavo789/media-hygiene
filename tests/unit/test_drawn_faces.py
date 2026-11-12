"""A face drawn by hand (0715): found in its box or the box itself, kept, drawn."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest
from PIL import Image

from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.constants import MediaKind
from media_hygiene.faces.align import TEMPLATE
from media_hygiene.faces.boxed import boxed_face, template_landmarks
from media_hygiene.faces.engine import FaceEngine
from media_hygiene.faces.models import FaceBox, PhotoFaces
from media_hygiene.index.drawn_faces import (
    DRAWN_FROM,
    add_drawn,
    forget_drawn,
    is_drawn,
)
from media_hygiene.index.face_rows import FaceStore, StoredFace
from media_hygiene.index.facts import FileFacts
from media_hygiene.index.repository import FactsRepository
from media_hygiene.person.drawing import (
    DRAWN_SHARPNESS,
    DRAWN_SIDE,
    NAMED_ONLY_SHARPNESS,
    DrawJob,
    draw_face,
    search_vector,
    usable,
)
from media_hygiene.person.forget_route import without_ids
from media_hygiene.scan.models import MediaFile
from tests.support.faces import FakeFinder, FakeRecipe, coloured, face_of

if TYPE_CHECKING:
    from numpy.typing import NDArray

MODEL = "test-model"


def embedder(pixels: NDArray[np.float32]) -> dict[str, NDArray[np.float32]]:
    """A fake SFace: the mean of each channel, then zeros."""
    vector = np.zeros((1, 128), dtype=np.float32)
    vector[0, :3] = pixels.mean(axis=(0, 2, 3))
    return {"fc1": vector}


def no_detector(pixels: NDArray[np.float32]) -> dict[str, NDArray[np.float32]]:
    """Never asked: a box needs no detection."""
    raise AssertionError(pixels.shape)


def test_the_template_points_fill_a_box_as_they_fill_the_crop() -> None:
    """A box of the crop's size, at the origin, gets the template itself."""
    points = np.asarray(template_landmarks(FaceBox(0, 0, 112, 112))).reshape(5, 2)
    assert np.allclose(points, TEMPLATE)


def test_a_box_is_described_by_the_engine_and_noise_is_not_usable() -> None:
    """Texture in the box: sharp, usable; a blank area: no sharpness, nothing usable."""
    rng = np.random.default_rng(1)
    noisy = Image.fromarray(rng.integers(0, 255, (200, 200, 3), dtype=np.uint8))
    engine = FaceEngine(no_detector, embedder)
    box = FaceBox(50, 50, 100, 100)
    sharp = boxed_face(engine, noisy, box)
    assert sharp is not None
    assert (sharp.box, sharp.score) == (box, 0.0)
    assert usable(sharp)
    blank = boxed_face(engine, Image.new("RGB", (200, 200), (128, 128, 128)), box)
    assert blank is not None
    assert not usable(blank)
    assert boxed_face(FakeFinder(), noisy, box) is None  # a finder without embedder


def test_usable_needs_both_the_side_and_the_sharpness() -> None:
    """Below either threshold, a drawn face says nothing of the person."""
    face = face_of(0, (int(DRAWN_SIDE), int(DRAWN_SIDE)))
    assert usable(face)
    assert not usable(face_of(0, (int(DRAWN_SIDE) - 1, 60)))
    blurred = dataclasses.replace(face_of(0, (60, 60)), sharpness=DRAWN_SHARPNESS - 1)
    assert not usable(blurred)


def test_a_box_on_a_face_finds_it_measured_in_the_photo(tmp_path: Path) -> None:
    """The detector finds the face in the part enlarged: measured in the photo."""
    photo = coloured(tmp_path / "red.png", 0, (200, 100))
    found = draw_face(DrawJob(photo, (0.25, 0.25, 0.5, 0.5), FakeRecipe()))
    assert found is not None
    assert found.searchable
    face = found.face
    assert face.box.x == pytest.approx(25, abs=1)  # the part: the box and its margin
    assert face.box.width == pytest.approx(150, abs=1)
    assert np.argmax(face.vector()) == 0


def test_a_box_on_a_blank_area_or_an_unreadable_photo_finds_nothing(
    tmp_path: Path,
) -> None:
    """Nobody in the box, and a finder that cannot describe a box: None."""
    dark = coloured(tmp_path / "dark.png", -1)
    assert draw_face(DrawJob(dark, (0.1, 0.1, 0.5, 0.5), FakeRecipe())) is None
    broken = tmp_path / "broken.jpg"
    broken.write_bytes(b"not a picture")
    assert draw_face(DrawJob(broken, (0.1, 0.1, 0.5, 0.5), FakeRecipe())) is None


def test_a_drawn_face_is_kept_flagged_and_survives_a_new_analysis(
    tmp_path: Path,
) -> None:
    """Numbered from DRAWN_FROM; the same version analysed again keeps it."""
    path = tmp_path / "a.jpg"
    with FactsRepository.open(tmp_path / "index.sqlite") as repository:
        connection = repository.connection
        drawn = face_of(1, (30, 30))
        assert add_drawn(connection, MODEL, (path, drawn)) is None  # not indexed
        repository.put(MediaFile(path, 10, 1, MediaKind.IMAGE), FileFacts())
        store = FaceStore(connection, MODEL)
        store.put(PhotoFaces(path, 10, 1, (face_of(0, (60, 60)),), 0.1))
        assert add_drawn(connection, MODEL, (path, drawn)) == DRAWN_FROM
        assert add_drawn(connection, MODEL, (path, drawn)) == DRAWN_FROM + 1
        store.put(PhotoFaces(path, 10, 1, (face_of(0, (60, 60)),), 0.1))  # re-audit
        numbers = [face.number for face in store.faces()]
        assert numbers == [0, DRAWN_FROM, DRAWN_FROM + 1]
        assert [is_drawn(number) for number in numbers] == [False, True, True]
        repository.put(MediaFile(path, 10, 2, MediaKind.IMAGE), FileFacts())
        store.put(PhotoFaces(path, 10, 2, (), 0.1))  # the photo changed: gone
        assert not store.faces()


def test_a_face_drawn_too_blurred_is_named_only_and_a_blank_one_is_no_face() -> None:
    """A baby's soft face: named, never searched from; a blank box: nothing."""
    box = FaceBox(0, 0, 60, 60)
    vector = b"\x01" * 8

    def stored(number: int, sharpness: float) -> StoredFace:
        return StoredFace(Path("/data/c/a.jpg"), number, box, 0.0, sharpness, vector)

    assert search_vector(stored(DRAWN_FROM, DRAWN_SHARPNESS - 1)) == b""
    assert search_vector(stored(DRAWN_FROM, DRAWN_SHARPNESS)) == vector
    assert search_vector(stored(0, 1.0)) == vector  # a face the audit found: as before
    engine = FaceEngine(no_detector, embedder)
    blank = boxed_face(engine, Image.new("RGB", (200, 200), (128, 128, 128)), box)
    assert blank is not None
    assert blank.sharpness < NAMED_ONLY_SHARPNESS


def test_two_boxes_overlap_by_their_intersection_over_their_union() -> None:
    """The same box: 1; apart: 0; half of one box shared: a third."""
    box = FaceBox(0, 0, 10, 10)
    assert box.overlap(box) == 1.0
    assert box.overlap(FaceBox(20, 20, 10, 10)) == 0.0
    assert box.overlap(FaceBox(5, 0, 10, 10)) == pytest.approx(50 / 150)
    assert FaceBox(0, 0, 0, 0).overlap(FaceBox(0, 0, 0, 0)) == 0.0


def test_only_a_face_drawn_is_forgotten_the_audits_stay(tmp_path: Path) -> None:
    """A face drawn by mistake leaves the index; a face the audit found never does."""
    path = tmp_path / "a.jpg"
    with FactsRepository.open(tmp_path / "index.sqlite") as repository:
        connection = repository.connection
        repository.put(MediaFile(path, 10, 1, MediaKind.IMAGE), FileFacts())
        store = FaceStore(connection, MODEL)
        store.put(PhotoFaces(path, 10, 1, (face_of(0, (60, 60)),), 0.1))
        number = add_drawn(connection, MODEL, (path, face_of(1, (30, 30))))
        assert number == DRAWN_FROM
        assert not forget_drawn(connection, MODEL, (path, 0))  # found by the audit
        assert not forget_drawn(connection, "other-model", (path, number))
        assert forget_drawn(connection, MODEL, (path, number))
        assert [face.number for face in store.faces()] == [0]
        assert not forget_drawn(connection, MODEL, (path, number))  # gone already


def test_a_face_forgotten_leaves_every_name_and_a_person_left_without_any() -> None:
    """Confirmed, ruled out, ignored: the id leaves them all; the others stay."""
    gone, kept = "/data/c/a.jpg#1000", "/data/c/a.jpg#0"
    section = PeopleSettings(
        person=(
            Person(name="Ann", faces=(gone,)),
            Person(name="Bob", faces=(kept,), rejected=(gone, kept)),
        ),
        ignored=(gone, "/data/c/b.jpg#0"),
    )
    after = without_ids(section, frozenset({gone}))
    assert [person.name for person in after.person] == ["Bob"]
    assert (after.person[0].faces, after.person[0].rejected) == ((kept,), (kept,))
    assert after.ignored == ("/data/c/b.jpg#0",)
