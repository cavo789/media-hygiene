"""A picture as an image model reads it, and the vectors' arithmetic.

Shared with the embeddings bench (`tests/measure/embeddings`), which compared the
models on the maintainer's photos (TODO 0221): the product reads a picture exactly
as the bench measured it.
"""

from __future__ import annotations

import json
import struct
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray
    from PIL import Image

_HEADER_BYTES: Final = 8
_SAFETENSORS_META: Final = "__metadata__"
_CHANNELS_FIRST: Final = (2, 0, 1)
_MAX_LEVEL: Final = 255.0


@dataclass(frozen=True, slots=True)
class Pixels:
    """How a model wants its picture: size, crop and colour scale."""

    side: int  # the square the model reads
    shortest: int  # shortest edge before a centre crop; 0: squashed to the square
    mean: tuple[float, float, float]
    std: tuple[float, float, float]
    resample: Image.Resampling


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
