"""Turn a picture or a search into a vector: the ONNX models, or a stub for the tests.

`onnxruntime` is in the image (faces); `tokenizers` is installed at run time, in a
temporary folder (README.md): both are imported by name, when a real model loads, so the
tests and the stub never need them.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import struct
from typing import TYPE_CHECKING, Any, Final, Protocol

import numpy as np

from .models import SPECS, fetch

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray
    from PIL import Image

    from .models import ModelSpec, Pixels, Words

STUB: Final = "stub"
STUB_DIMENSIONS: Final = 16
_STUB_THUMB: Final = (8, 8)
_HEADER_BYTES: Final = 8
_SAFETENSORS_META: Final = "__metadata__"
_ERRORS_ONLY: Final = 3
_PROVIDERS: Final = ("CPUExecutionProvider",)
_CHANNELS_FIRST: Final = (2, 0, 1)
_MAX_LEVEL: Final = 255.0
_CLS: Final = 0
_TWO_D: Final = 2


class Embedder(Protocol):
    """What the bench asks of a model."""

    @property
    def reads_text(self) -> bool:
        """Whether searches can be compared with its pictures."""
        ...

    def image(self, picture: Image.Image) -> NDArray[np.float32]:
        """The unit vector of a picture."""
        ...

    def text(self, query: str) -> NDArray[np.float32]:
        """The unit vector of a search, in the space of the pictures."""
        ...


def unit(vector: NDArray[np.float32]) -> NDArray[np.float32]:
    """Scale a vector to length one (a zero vector stays zero).

    Args:
        vector: Any vector.

    Returns:
        The same direction, length one.
    """
    length = float(np.linalg.norm(vector))
    return vector if length == 0.0 else (vector / length).astype(np.float32)


def pixels_of(picture: Image.Image, pixels: Pixels) -> NDArray[np.float32]:
    """Resize, crop and scale a picture as a model was trained to read it.

    Args:
        picture: The decoded picture, upright.
        pixels: The model's way.

    Returns:
        A `3 x side x side` tensor.
    """
    rgb = picture.convert("RGB")
    side = pixels.side
    if pixels.shortest:
        scale = pixels.shortest / min(rgb.size)
        width = max(side, round(rgb.width * scale))
        height = max(side, round(rgb.height * scale))
        rgb = rgb.resize((width, height), pixels.resample)
        left, top = (width - side) // 2, (height - side) // 2
        rgb = rgb.crop((left, top, left + side, top + side))
    else:
        rgb = rgb.resize((side, side), pixels.resample)
    array = np.asarray(rgb, dtype=np.float32) / _MAX_LEVEL
    mean = np.asarray(pixels.mean, dtype=np.float32)
    std = np.asarray(pixels.std, dtype=np.float32)
    return ((array - mean) / std).transpose(_CHANNELS_FIRST).astype(np.float32)


def read_projection(path: Path) -> NDArray[np.float32]:
    """Read the one weight matrix of a safetensors file (no bias, as its config says).

    Args:
        path: The file.

    Returns:
        The matrix, `out x in`.
    """
    data = path.read_bytes()
    (length,) = struct.unpack("<Q", data[:_HEADER_BYTES])
    header = json.loads(data[_HEADER_BYTES : _HEADER_BYTES + length])
    (entry,) = (value for key, value in header.items() if key != _SAFETENSORS_META)
    start, end = entry["data_offsets"]
    body = data[_HEADER_BYTES + length + start : _HEADER_BYTES + length + end]
    return np.frombuffer(body, dtype=np.float32).reshape(entry["shape"])


def _first_vector(output: NDArray[np.float32]) -> NDArray[np.float32]:
    """The vector of one picture: pooled already, or its first token (CLS).

    Args:
        output: The model's output for a batch of one.

    Returns:
        One vector.
    """
    vector: NDArray[np.float32] = (
        output[0] if output.ndim == _TWO_D else output[0, _CLS]
    )
    return vector


class StubEmbedder:
    """Random vectors, the same for the same pixels: the tests' model, no download."""

    reads_text = True

    def image(self, picture: Image.Image) -> NDArray[np.float32]:
        """A vector drawn from the picture's thumbnail.

        Args:
            picture: The picture.

        Returns:
            A unit vector.
        """
        thumb = picture.convert("RGB").resize(_STUB_THUMB).tobytes()
        return _drawn(thumb)

    def text(self, query: str) -> NDArray[np.float32]:
        """A vector drawn from the words.

        Args:
            query: The search.

        Returns:
            A unit vector.
        """
        return _drawn(query.encode())


def _drawn(seed: bytes) -> NDArray[np.float32]:
    """A random unit vector, always the same for the same bytes.

    Args:
        seed: The bytes.

    Returns:
        The vector.
    """
    generator = np.random.default_rng(int.from_bytes(hashlib.sha256(seed).digest()))
    return unit(generator.standard_normal(STUB_DIMENSIONS).astype(np.float32))


class OnnxEmbedder:
    """A model of `models.SPECS`, run by the ONNX runtime on the CPU."""

    def __init__(self, spec: ModelSpec, root: Path, threads: int) -> None:
        """Load the image model, and the text model when it has one.

        Args:
            spec: The model.
            root: The models folder (its files downloaded already).
            threads: The threads the runtime may use.
        """
        runtime: Any = importlib.import_module("onnxruntime")
        options = runtime.SessionOptions()
        options.log_severity_level = _ERRORS_ONLY
        options.intra_op_num_threads = threads
        options.inter_op_num_threads = 1
        self._spec = spec
        self._image: Any = runtime.InferenceSession(
            str(fetch(spec.image, root)), options, providers=_PROVIDERS
        )
        self._text = (
            None if spec.words is None else _TextSide(spec.words, root, options)
        )

    @property
    def reads_text(self) -> bool:
        """Whether the model has a text side.

        Returns:
            True for SigLIP 2 and CLIP.
        """
        return self._text is not None

    def image(self, picture: Image.Image) -> NDArray[np.float32]:
        """The vector of a picture.

        Args:
            picture: The picture, upright.

        Returns:
            A unit vector.
        """
        tensor = pixels_of(picture, self._spec.pixels)[None]
        (output,) = self._image.run([self._spec.image_output], {"pixel_values": tensor})
        return unit(_first_vector(output))

    def text(self, query: str) -> NDArray[np.float32]:
        """The vector of a search.

        Args:
            query: The words.

        Returns:
            A unit vector.

        Raises:
            ValueError: The model reads no text (DINOv2).
        """
        if self._text is None:
            message = f"{self._spec.name} reads no text"
            raise ValueError(message)
        return self._text.vector(query)


class _TextSide:
    """The tokenizer and text model of a model, with its pooling."""

    def __init__(self, words: Words, root: Path, options: object) -> None:
        """Load them.

        Args:
            words: How the model reads a search.
            root: The models folder.
            options: The runtime's session options.
        """
        runtime: Any = importlib.import_module("onnxruntime")
        tokenizers: Any = importlib.import_module("tokenizers")
        self._words = words
        self._tokenizer: Any = tokenizers.Tokenizer.from_file(
            str(fetch(words.tokenizer, root))
        )
        self._tokenizer.no_padding()
        self._tokenizer.enable_truncation(words.max_tokens)
        self._session: Any = runtime.InferenceSession(
            str(fetch(words.model, root)), options, providers=_PROVIDERS
        )
        self._inputs = {str(item.name) for item in self._session.get_inputs()}
        dense = words.dense
        self._dense = None if dense is None else read_projection(fetch(dense, root))

    def vector(self, query: str) -> NDArray[np.float32]:
        """The vector of a search.

        Args:
            query: The words.

        Returns:
            A unit vector.
        """
        ids = self.ids(query)
        feed = {"input_ids": np.asarray([ids], dtype=np.int64)}
        mask = np.asarray([[1] * len(ids)], dtype=np.int64)
        if "attention_mask" in self._inputs:
            feed["attention_mask"] = mask
        (output,) = self._session.run([self._words.output], feed)
        if self._dense is None:
            return unit(_first_vector(output))
        pooled = output[0].mean(axis=0)
        return unit((self._dense @ pooled).astype(np.float32))

    def ids(self, query: str) -> list[int]:
        """The tokens of a search, ended and padded as the model expects.

        Args:
            query: The words.

        Returns:
            The token ids.
        """
        words = self._words
        text = query.lower() if words.lowercase else query
        ids = [int(token) for token in self._tokenizer.encode(text).ids]
        if words.end:
            end = int(self._tokenizer.token_to_id(words.end))
            ids = [*ids[: words.max_tokens - 1], end] if ids[-1:] != [end] else ids
        if words.pad_to:
            pad = int(self._tokenizer.token_to_id("<pad>"))
            ids = ids + [pad] * (words.pad_to - len(ids))
        return ids


def load_embedder(name: str, root: Path, threads: int) -> Embedder:
    """Load a model by name.

    Args:
        name: A name of `models.SPECS`, or `stub`.
        root: The models folder.
        threads: The threads the runtime may use.

    Returns:
        The model.
    """
    if name == STUB:
        return StubEmbedder()
    return OnnxEmbedder(SPECS[name], root, threads)
