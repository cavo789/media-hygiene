"""The model files: downloaded once, their digest checked; never a real download."""

from __future__ import annotations

import hashlib
import io
import sys
import types
import urllib.request
from typing import TYPE_CHECKING

import numpy as np
import pytest

from media_hygiene.errors import FaceModelError
from media_hygiene.faces.onnx_runner import RUNTIME_MODULE, onnx_runner
from media_hygiene.faces.weights import Fetch, ModelFile, download, ensure_model

if TYPE_CHECKING:
    from pathlib import Path

CONTENT = b"not really a model"
MODEL = ModelFile("model.onnx", "https://example.invalid/model.onnx", "")
GOOD = ModelFile(MODEL.name, MODEL.url, hashlib.sha256(CONTENT).hexdigest())


def writer(content: bytes, calls: list[str]) -> Fetch:
    """A fake download writing fixed bytes.

    Args:
        content: What it writes.
        calls: Receives each URL asked for.

    Returns:
        The fetch.
    """

    def fetch(url: str, target: Path) -> None:
        calls.append(url)
        target.write_bytes(content)

    return fetch


def test_a_missing_model_is_downloaded_once(tmp_path: Path) -> None:
    """The first call downloads; the second finds the file and its digest."""
    calls: list[str] = []
    first = ensure_model(tmp_path / "models", GOOD, writer(CONTENT, calls))
    again = ensure_model(tmp_path / "models", GOOD, writer(CONTENT, calls))
    assert first == again == tmp_path / "models" / "model.onnx"
    assert first.read_bytes() == CONTENT
    assert calls == [GOOD.url]


def test_another_file_is_refused_and_deleted(tmp_path: Path) -> None:
    """A download with another digest leaves nothing behind."""
    with pytest.raises(FaceModelError, match="not the expected file"):
        ensure_model(tmp_path, GOOD, writer(b"tampered", []))
    assert not list(tmp_path.iterdir())


def test_a_failed_download_says_where_to_put_the_file(tmp_path: Path) -> None:
    """No network: the error names the URL and the place to save it by hand."""

    def offline(_url: str, target: Path) -> None:
        target.write_bytes(b"partial")
        raise OSError("no route to host")  # noqa: EM101, TRY003

    with pytest.raises(FaceModelError) as caught:
        ensure_model(tmp_path, GOOD, offline)
    assert "no route to host" in caught.value.message
    assert GOOD.url in (caught.value.tip or "")
    assert not list(tmp_path.iterdir())


def test_download_refuses_a_plain_http_url(tmp_path: Path) -> None:
    """Only HTTPS is fetched."""
    with pytest.raises(ValueError, match="HTTPS"):
        download("http://example.invalid/model.onnx", tmp_path / "x")


def test_download_copies_the_answer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The answer's bytes are written to the target (no network here)."""
    monkeypatch.setattr(
        urllib.request, "urlopen", lambda *_a, **_k: io.BytesIO(CONTENT)
    )
    download(GOOD.url, tmp_path / "model.onnx")
    assert (tmp_path / "model.onnx").read_bytes() == CONTENT


def test_without_the_runtime_the_error_says_how_to_install_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """No `onnxruntime`: one sentence, no traceback."""
    monkeypatch.setitem(sys.modules, RUNTIME_MODULE, None)
    with pytest.raises(FaceModelError, match="ONNX runtime"):
        onnx_runner(tmp_path / "model.onnx")


class _Named:
    """An input or output of the fake session."""

    def __init__(self, name: str) -> None:
        self.name = name


class _Session:
    """A fake inference session: doubles its input."""

    def __init__(self, _path: str, options: object, providers: tuple[str, ...]) -> None:
        assert providers == ("CPUExecutionProvider",)
        assert options.intra_op_num_threads == 1  # type: ignore[attr-defined]

    def get_inputs(self) -> list[_Named]:
        """The input."""
        return [_Named("input")]

    def get_outputs(self) -> list[_Named]:
        """The output."""
        return [_Named("out")]

    def run(self, _names: object, feed: dict[str, np.ndarray]) -> list[np.ndarray]:
        """Double the input."""
        return [feed["input"] * 2]


def test_the_runner_names_the_outputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The runtime's session is run on one thread, its outputs returned by name."""
    fake = types.SimpleNamespace(
        SessionOptions=types.SimpleNamespace, InferenceSession=_Session
    )
    monkeypatch.setitem(sys.modules, RUNTIME_MODULE, fake)
    run = onnx_runner(tmp_path / "model.onnx")
    assert run(np.ones(2, dtype=np.float32))["out"].tolist() == [2.0, 2.0]
