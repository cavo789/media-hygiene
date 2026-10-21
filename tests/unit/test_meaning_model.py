"""The CLIP model of search by meaning: its files in the cache, its two sides.

No download and no ONNX: the files are written by a fake fetch, the runtime and the
tokenizer are fakes answering what the real ones answer (shapes, names).
"""

from __future__ import annotations

import hashlib
import json
import struct
import sys
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import numpy as np
import pytest
from PIL import Image

from media_hygiene.errors import FaceModelError
from media_hygiene.faces.weights import MODELS_DIR_NAME, ModelFile
from media_hygiene.meaning import files
from media_hygiene.meaning.clip import DIMENSIONS, FILES, PIXELS
from media_hygiene.meaning.embedder import ClipImages, ClipWords
from media_hygiene.meaning.files import ClipFiles, clip_files, clip_known, clip_present
from media_hygiene.meaning.pixels import pixels_of

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray


def _fake_files(monkeypatch: pytest.MonkeyPatch) -> dict[str, bytes]:
    """Replace the four files by small ones whose digests are known."""
    contents: dict[str, bytes] = {}
    for model in FILES:
        content = model.name.encode()
        contents[model.url] = content
        fake = ModelFile(model.name, model.url, hashlib.sha256(content).hexdigest())
        for constant in ("VISION", "TEXT", "TOKENIZER", "DENSE"):
            if getattr(files, constant) is model:
                monkeypatch.setattr(files, constant, fake)
    return contents


def test_the_files_are_downloaded_once_into_the_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Missing: fetched and checked; present: read as they are, not fetched."""
    contents = _fake_files(monkeypatch)
    fetched: list[str] = []

    def fetch(url: str, target: Path) -> None:
        fetched.append(url)
        target.write_bytes(contents[url])

    assert not clip_present(tmp_path)
    found = clip_files(tmp_path, fetch)
    assert clip_present(tmp_path)
    assert len(fetched) == len(FILES)
    assert found == clip_known(tmp_path)
    assert found.vision.parent == tmp_path / MODELS_DIR_NAME
    assert clip_files(tmp_path, fetch) == found
    assert len(fetched) == len(FILES)


def test_an_altered_download_is_refused(tmp_path: Path) -> None:
    """Another file than the pinned one is deleted, and said."""

    def fetch(_url: str, target: Path) -> None:
        target.write_bytes(b"tampered")

    with pytest.raises(FaceModelError, match="not the expected file"):
        clip_files(tmp_path, fetch)
    assert not clip_present(tmp_path)


def test_a_build_without_the_runtime_says_so(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No `tokenizers` (or `onnxruntime`): one sentence, never a traceback."""
    monkeypatch.setitem(sys.modules, "tokenizers", None)  # import raises
    with pytest.raises(FaceModelError, match="tokenizers is not installed"):
        ClipWords(clip_known(tmp_path), 1)


class _Session:
    """An ONNX session: the image model's or the text model's answer."""

    def __init__(self, path: str, options: object, providers: object) -> None:
        """Load nothing."""
        del options, providers
        self.path = path

    def get_inputs(self) -> list[SimpleNamespace]:
        """The text model's inputs."""
        return [
            SimpleNamespace(name="input_ids"),
            SimpleNamespace(name="attention_mask"),
        ]

    def run(self, names: list[str], feed: dict[str, NDArray[Any]]) -> list[Any]:
        """Answer with the real models' shapes."""
        if names == ["image_embeds"]:
            assert feed["pixel_values"].shape == (1, 3, 224, 224)
            return [np.full((1, DIMENSIONS), 2.0, dtype=np.float32)]
        assert feed["attention_mask"].shape == feed["input_ids"].shape
        tokens = feed["input_ids"].shape[1]
        return [np.ones((1, tokens, 768), dtype=np.float32)]


class _Tokenizer:
    """A tokenizer reading a file: one token per word."""

    def __init__(self) -> None:
        """No truncation yet."""
        self.length = 0

    @classmethod
    def from_file(cls, path: str) -> _Tokenizer:
        """Read nothing."""
        del path
        return cls()

    def no_padding(self) -> None:
        """Nothing to pad."""

    def enable_truncation(self, length: int) -> None:
        """Remember the length."""
        self.length = length

    def encode(self, text: str) -> SimpleNamespace:
        """One token per word, and the two ends."""
        return SimpleNamespace(ids=list(range(len(text.split()) + 2)))


def test_both_sides_give_unit_vectors_of_the_same_space(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A picture: 512 values; a search: averaged, projected to 512, unit length."""
    dense = tmp_path / "dense.safetensors"
    weights = np.ones((DIMENSIONS, 768), dtype=np.float32)
    header = json.dumps(
        {
            "linear.weight": {
                "dtype": "F32",
                "shape": [DIMENSIONS, 768],
                "data_offsets": [0, weights.nbytes],
            }
        }
    ).encode()
    dense.write_bytes(struct.pack("<Q", len(header)) + header + weights.tobytes())
    paths = ClipFiles(
        tmp_path / "v.onnx", tmp_path / "t.onnx", tmp_path / "tok.json", dense
    )
    runtime = SimpleNamespace(SessionOptions=SimpleNamespace, InferenceSession=_Session)
    monkeypatch.setitem(sys.modules, "onnxruntime", runtime)
    monkeypatch.setitem(
        sys.modules, "tokenizers", SimpleNamespace(Tokenizer=_Tokenizer)
    )
    picture = ClipImages(paths, 2).image(Image.new("RGB", (640, 480), (10, 200, 30)))
    words = ClipWords(paths, 2).text("un chat sur un canapé")
    for vector in (picture, words):
        assert vector.shape == (DIMENSIONS,)
        assert np.isclose(float(np.linalg.norm(vector)), 1.0)
    assert np.isclose(float(picture @ words), 1.0)


def test_the_picture_is_read_as_the_bench_measured_it() -> None:
    """Shortest side to 224, centre crop, CLIP's colour scale."""
    tensor = pixels_of(Image.new("RGB", (640, 480), (255, 255, 255)), PIXELS)
    assert tensor.shape == (3, 224, 224)
    assert np.allclose(tensor[0], (1.0 - PIXELS.mean[0]) / PIXELS.std[0])
