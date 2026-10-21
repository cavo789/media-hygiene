"""Turn a picture or a search into a vector of the model, on the CPU.

`onnxruntime` (in the image for the faces) and `tokenizers` are imported by name when
a model loads: no other command pays for them, and a build without them says so in
one sentence. The image side serves `tags`, the text side `search`: each loads only
what it needs (the text model alone is 539 MB).
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any, Final, Protocol

import numpy as np

from media_hygiene.errors import FaceModelError
from media_hygiene.i18n import _
from media_hygiene.meaning.clip import IMAGE_OUTPUT, MAX_TOKENS, PIXELS, TEXT_OUTPUT
from media_hygiene.meaning.pixels import pixels_of, read_projection, unit

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray
    from PIL import Image

    from media_hygiene.meaning.files import ClipFiles

_PROVIDERS: Final = ("CPUExecutionProvider",)
_ERRORS_ONLY: Final = 3  # the runtime's log level: no warning about the model's graph
_RUNTIME: Final = "onnxruntime"
_TOKENIZERS: Final = "tokenizers"
_MASK: Final = "attention_mask"


class ImageReader(Protocol):
    """What `tags` asks of the model: the vector of a picture."""

    def image(self, picture: Image.Image) -> NDArray[np.float32]:
        """The unit vector of a picture.

        Args:
            picture: The picture, upright.
        """
        ...


class TextReader(Protocol):
    """What `search` asks of the model: the vector of a search."""

    def text(self, query: str) -> NDArray[np.float32]:
        """The unit vector of a search, in the space of the pictures.

        Args:
            query: The words.
        """
        ...


def _module(name: str) -> Any:  # noqa: ANN401 - untyped third-party modules
    """Import a module the model needs, or say in one sentence that it is missing.

    Args:
        name: `onnxruntime` or `tokenizers`.

    Returns:
        The module.

    Raises:
        FaceModelError: It is not installed in this build.
    """
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError as exc:
        raise FaceModelError(
            _("This build cannot search by meaning: {module} is not installed.").format(
                module=name
            ),
            _("Use the published image, or install the dependencies again: uv sync."),
        ) from exc


def _session(model: Path, threads: int) -> Any:  # noqa: ANN401 - onnxruntime's
    """Load a model file on the CPU.

    Args:
        model: The `.onnx` file.
        threads: How many threads it may use.

    Returns:
        The runtime's session.
    """
    runtime = _module(_RUNTIME)
    options = runtime.SessionOptions()
    options.log_severity_level = _ERRORS_ONLY
    options.intra_op_num_threads = threads
    options.inter_op_num_threads = 1
    return runtime.InferenceSession(str(model), options, providers=_PROVIDERS)


class ClipImages:
    """The image model: one picture at a time, on `threads` CPU threads."""

    def __init__(self, files: ClipFiles, threads: int) -> None:
        """Load it.

        Args:
            files: The model's files, downloaded.
            threads: How many threads it may use.
        """
        self._session = _session(files.vision, threads)

    def image(self, picture: Image.Image) -> NDArray[np.float32]:
        """The vector of a picture.

        Args:
            picture: The picture, upright.

        Returns:
            A unit vector.
        """
        tensor = pixels_of(picture, PIXELS)[None]
        (output,) = self._session.run([IMAGE_OUTPUT], {"pixel_values": tensor})
        return unit(np.asarray(output[0], dtype=np.float32))


class ClipWords:
    """The multilingual text model, its tokenizer and its projection."""

    def __init__(self, files: ClipFiles, threads: int) -> None:
        """Load them.

        Args:
            files: The model's files, downloaded.
            threads: How many threads it may use.
        """
        tokenizer = _module(_TOKENIZERS).Tokenizer.from_file(str(files.tokenizer))
        tokenizer.no_padding()
        tokenizer.enable_truncation(MAX_TOKENS)
        self._tokenizer: Any = tokenizer
        self._session: Any = _session(files.text, threads)
        self._masked = _MASK in {str(item.name) for item in self._session.get_inputs()}
        self._dense = read_projection(files.dense)

    def text(self, query: str) -> NDArray[np.float32]:
        """The vector of a search: its tokens averaged, then projected.

        Args:
            query: The words.

        Returns:
            A unit vector, in the space of the pictures.
        """
        ids = [int(token) for token in self._tokenizer.encode(query).ids]
        feed = {"input_ids": np.asarray([ids], dtype=np.int64)}
        if self._masked:
            feed[_MASK] = np.ones((1, len(ids)), dtype=np.int64)
        (output,) = self._session.run([TEXT_OUTPUT], feed)
        pooled = np.asarray(output[0], dtype=np.float32).mean(axis=0)
        return unit((self._dense @ pooled).astype(np.float32))
