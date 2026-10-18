"""The embeddings bench (TODO 0220): sampling, ranking, pairs and pages, a stub model.

Synthetic pictures only, no download: the stub draws a random vector from each picture's
pixels, so the same picture always gets the same vector.
"""

from __future__ import annotations

import json
import struct
from typing import TYPE_CHECKING

import numpy as np
import pytest
from PIL import Image, ImageDraw

from tests.measure.embeddings import measure
from tests.measure.embeddings.embedders import (
    STUB,
    STUB_DIMENSIONS,
    StubEmbedder,
    pixels_of,
    read_projection,
    unit,
)
from tests.measure.embeddings.models import (
    CLIP,
    DINOV2,
    SIGLIP2,
    SPECS,
    Remote,
    size_mb,
)
from tests.measure.embeddings.pages import write_pages
from tests.measure.embeddings.ranking import (
    PAIRS,
    SEARCH,
    SHOWN,
    Bench,
    best,
    closest_pairs,
    hashes_of,
    near_pairs,
    ranked,
    search_hits,
)
from tests.measure.embeddings.runs import (
    Job,
    ModelRun,
    Timing,
    read_queries,
    run_job,
    sample,
)

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray

_SIZE = (96, 72)


def _picture(path: Path, seed: int) -> Path:
    """Write a synthetic JPEG: a background and a few ellipses drawn from `seed`."""
    generator = np.random.default_rng(seed)
    colours = [tuple(int(c) for c in generator.integers(0, 256, 3)) for _ in range(5)]
    image = Image.new("RGB", _SIZE, colours[0])
    draw = ImageDraw.Draw(image)
    for colour in colours[1:]:
        left, top = (int(v) for v in generator.integers(0, 60, 2))
        draw.ellipse((left, top, left + 30, top + 25), fill=colour)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, quality=90)
    return path


def _photos(root: Path, count: int) -> tuple[Path, ...]:
    """Write `count` different synthetic photos below `root`."""
    return tuple(_picture(root / f"p{at:02d}.jpg", at) for at in range(count))


def _timing() -> Timing:
    """Costs of no importance."""
    return Timing(0.1, 0.01, 0.02, 0.003, 100.0, 0.0, 2, 0)


def _run(images: NDArray[np.float32], texts: NDArray[np.float32] | None) -> ModelRun:
    """A model's run from given vectors, every photo readable."""
    readable = np.ones(len(images), dtype=np.bool_)
    return ModelRun(STUB, images.astype(np.float32), readable, texts, _timing())


def test_sample_is_repeatable_and_skips_what_is_no_photo(tmp_path: Path) -> None:
    """The same seed, the same photos; #recycle, @eaDir and other files left out."""
    photos = _photos(tmp_path / "photos", 12)
    _picture(tmp_path / "photos" / "#recycle" / "gone.jpg", 99)
    _picture(tmp_path / "photos" / "@eaDir" / "thumb.jpg", 98)
    (tmp_path / "photos" / "notes.txt").write_text("not a photo", encoding="utf-8")

    first = sample(tmp_path / "photos", 5, 7)

    assert first == sample(tmp_path / "photos", 5, 7)
    assert len(first) == 5
    assert list(first) == sorted(first)
    assert set(first) <= set(photos)
    assert sample(tmp_path / "photos", 5, 8) != first
    assert sample(tmp_path / "photos", 100, 7) == tuple(sorted(photos))


def test_read_queries_leaves_out_comments_and_blank_lines(tmp_path: Path) -> None:
    """A searches file saved by Notepad (BOM) gives its searches only."""
    path = tmp_path / "queries.txt"
    text = "﻿# mes recherches\ngâteau d'anniversaire\n\n  plage  \n#x\n"
    path.write_text(text, encoding="utf-8")

    assert read_queries(path) == ("gâteau d'anniversaire", "plage")


def test_stub_gives_the_same_vector_to_the_same_pixels(tmp_path: Path) -> None:
    """The stub's vectors are unit vectors, the same for the same picture."""
    first, second = _photos(tmp_path, 2)
    model = StubEmbedder()

    one = model.image(Image.open(first))

    assert one.shape == (STUB_DIMENSIONS,)
    assert np.isclose(np.linalg.norm(one), 1.0)
    assert np.array_equal(one, model.image(Image.open(first)))
    assert not np.array_equal(one, model.image(Image.open(second)))
    assert np.array_equal(model.text("plage"), model.text("plage"))


def test_unit_keeps_a_zero_vector() -> None:
    """Scaling never divides by zero."""
    zero = np.zeros(3, dtype=np.float32)

    assert np.array_equal(unit(zero), zero)
    assert np.allclose(unit(np.asarray([3.0, 4.0], dtype=np.float32)), [0.6, 0.8])


@pytest.mark.parametrize("name", [SIGLIP2.name, CLIP.name, DINOV2.name])
def test_pixels_of_gives_the_square_each_model_reads(name: str) -> None:
    """Each model gets its square, scaled by its own mean and spread."""
    model = SPECS[name]
    picture = Image.new("RGB", (400, 300), (255, 0, 0))

    tensor = pixels_of(picture, model.pixels)

    side = model.pixels.side
    assert tensor.shape == (3, side, side)
    assert tensor.dtype == np.float32
    red = (1.0 - model.pixels.mean[0]) / model.pixels.std[0]
    assert np.allclose(tensor[0], red, atol=1e-5)


def test_read_projection_reads_the_one_matrix(tmp_path: Path) -> None:
    """The projection of the multilingual text model is read without safetensors."""
    weights = np.arange(6, dtype=np.float32).reshape(2, 3)
    header = json.dumps(
        {
            "__metadata__": {"format": "pt"},
            "linear.weight": {"dtype": "F32", "shape": [2, 3], "data_offsets": [0, 24]},
        }
    ).encode()
    path = tmp_path / "model.safetensors"
    path.write_bytes(struct.pack("<Q", len(header)) + header + weights.tobytes())

    assert np.array_equal(read_projection(path), weights)


def test_models_name_pinned_files_and_their_licences(tmp_path: Path) -> None:
    """Every file is pinned to a revision; the size counts the files downloaded."""
    for spec in SPECS.values():
        assert spec.licence
        for remote in spec.remotes:
            assert remote.url.startswith("https://huggingface.co/")
            assert len(remote.revision) == 40
    assert len(CLIP.remotes) == 4
    assert DINOV2.words is None
    remote = Remote("owner/name", "0" * 40, "onnx/model.onnx")
    assert remote.local(tmp_path) == tmp_path / "owner" / "name" / "onnx" / "model.onnx"
    assert size_mb(DINOV2, tmp_path) == 0.0
    target = DINOV2.image.local(tmp_path)
    target.parent.mkdir(parents=True)
    target.write_bytes(b"x" * 2_000_000)
    assert size_mb(DINOV2, tmp_path) == 2.0


def test_best_ranks_the_closest_photos_and_skips_unreadable_ones() -> None:
    """A search's photos come closest first, an unreadable photo never."""
    images = np.eye(4, dtype=np.float32)
    texts = np.asarray([[0.0, 0.9, 0.1, 0.0]], dtype=np.float32)
    run = _run(images, texts)
    unreadable = ModelRun(
        STUB,
        images,
        np.asarray([True, False, True, True], dtype=np.bool_),
        texts,
        _timing(),
    )

    assert best(texts, run) == ((1, 2, 0, 3),)
    assert best(texts, unreadable) == ((2, 0, 3),)


def test_best_shows_at_most_the_first_pictures() -> None:
    """A search shows 24 pictures at most."""
    images = np.eye(SHOWN + 5, dtype=np.float32)
    texts = np.ones((1, SHOWN + 5), dtype=np.float32)

    assert len(best(texts, _run(images, texts))[0]) == SHOWN


def test_closest_pairs_leaves_out_what_the_audit_finds() -> None:
    """The pairs come most alike first, the audit's near duplicates left out."""
    images = np.asarray(
        [[1.0, 0.0], [1.0, 0.0], [0.8, 0.6], [0.0, 1.0]], dtype=np.float32
    )
    run = _run(images, None)

    every = closest_pairs(run, frozenset())
    left = closest_pairs(run, frozenset({(0, 1)}))

    assert (every[0].first, every[0].second) == (0, 1)
    assert np.isclose(every[0].similarity, 1.0)
    assert (0, 1) not in {(pair.first, pair.second) for pair in left}
    assert len(every) == 6
    assert [pair.similarity for pair in every] == sorted(
        (pair.similarity for pair in every), reverse=True
    )


def test_closest_pairs_stops_at_its_count() -> None:
    """A model shows 50 pairs at most."""
    generator = np.random.default_rng(3)
    images = generator.standard_normal((20, 8)).astype(np.float32)

    assert len(closest_pairs(_run(images, None), frozenset())) == PAIRS


def test_near_pairs_finds_an_exact_copy_only(tmp_path: Path) -> None:
    """The audit's hash test pairs a copy, not different pictures nor a broken file."""
    photos = _photos(tmp_path, 3)
    copy = tmp_path / "copy.jpg"
    copy.write_bytes(photos[0].read_bytes())
    broken = tmp_path / "broken.jpg"
    broken.write_bytes(b"not a jpeg")

    hashes = hashes_of((*photos, copy, broken))

    assert hashes[-1] is None
    assert near_pairs(hashes) == frozenset({(0, 3)})


def test_run_job_embeds_every_readable_photo(tmp_path: Path) -> None:
    """A run embeds the photos and the searches, counts what it could not read."""
    photos = _photos(tmp_path / "photos", 4)
    broken = tmp_path / "photos" / "broken.jpg"
    broken.write_bytes(b"not a jpeg")
    job = Job(STUB, tmp_path / "models", (*photos, broken), ("plage", "neige"), 2)

    run = run_job(job)

    assert run.images.shape == (5, STUB_DIMENSIONS)
    assert run.readable.tolist() == [True, True, True, True, False]
    assert run.texts is not None
    assert run.texts.shape == (2, STUB_DIMENSIONS)
    assert run.timing.failed == 1
    assert run.timing.threads == 2
    assert run.timing.peak_mb > 0
    assert run.timing.model_mb == 0.0


def test_search_hits_is_none_without_an_index(tmp_path: Path) -> None:
    """No index, or an unreadable one: no column of today's search."""
    assert search_hits(tmp_path / "index.sqlite", ("plage",), ()) is None
    (tmp_path / "broken.sqlite").write_bytes(b"not an index")
    assert search_hits(tmp_path / "broken.sqlite", ("plage",), ()) is None


def _bench(tmp_path: Path) -> Bench:
    """A bench of six photos, two searches, the stub model, today's search given."""
    photos = _photos(tmp_path / "photos", 6)
    queries = ("gâteau <d'anniversaire>", "plage")
    run = run_job(Job(STUB, tmp_path / "models", photos, queries, 1))
    return Bench(photos, queries, (run,), ((2, 0), ()))


def test_ranked_puts_today_search_beside_the_models(tmp_path: Path) -> None:
    """Today's search is one more column beside the models."""
    result = ranked(_bench(tmp_path))

    assert set(result.answers[0]) == {STUB, SEARCH}
    assert result.answers[0][SEARCH] == (2, 0)
    assert len(result.answers[1][STUB]) == 6
    assert len(result.pairs[STUB]) == 15


def test_pages_show_every_picture_with_a_box(tmp_path: Path) -> None:
    """Every picture shown has its box; the words are escaped; thumbnails are small."""
    out = tmp_path / "out"

    index = write_pages(ranked(_bench(tmp_path)), out)

    assert index == out / "index.html"
    queries = (out / "queries.html").read_text(encoding="utf-8")
    pairs = (out / "pairs.html").read_text(encoding="utf-8")
    summary = index.read_text(encoding="utf-8")
    assert queries.count('type="checkbox"') == 6 + 2 + 6
    assert pairs.count('type="checkbox"') == 15
    assert "gâteau &lt;d&#39;anniversaire&gt;" in queries
    assert "Nothing found." in queries
    assert "Stub (random vectors, tests only)" in summary
    assert "Today&#39;s search" in queries
    assert len(list((out / "thumbs").glob("*.jpg"))) == 6
    with Image.open(out / "thumbs" / "000000.jpg") as thumb:
        assert max(thumb.size) <= 320


def test_main_writes_the_pages_with_the_stub(tmp_path: Path) -> None:
    """The command line runs the stub in its own process and writes the pages."""
    _photos(tmp_path / "photos", 5)
    queries = tmp_path / "queries.txt"
    queries.write_text("plage\nneige\n", encoding="utf-8")
    arguments = [
        f"--photos={tmp_path / 'photos'}",
        f"--queries={queries}",
        f"--models-dir={tmp_path / 'models'}",
        f"--out={tmp_path / 'out'}",
        f"--models={STUB}",
        "--cpus=1",
        f"--index={tmp_path / 'none.sqlite'}",
    ]

    assert measure.main(arguments) == 0

    assert (tmp_path / "out" / "pairs.html").is_file()
    assert not (tmp_path / "models").exists()
