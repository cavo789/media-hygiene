"""The two model files: downloaded once into the cache, checked by their SHA-256.

They come from OpenCV Zoo at a pinned commit: YuNet (MIT, 230 KB) finds the faces,
SFace (Apache 2.0, 37 MB) describes them. A file whose digest differs is never used:
it is deleted and the download is told as failed. Nothing about the photos is sent.
Search by meaning (`meaning.clip`) downloads its files the same way.
"""

from __future__ import annotations

import hashlib
import shutil
import urllib.request
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import FaceModelError
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

MODELS_DIR_NAME: Final = "models"
_ZOO: Final = "https://github.com/opencv/opencv_zoo/raw"
_TIMEOUT: Final = 60.0  # seconds without an answer
_CHUNK: Final = 1 << 20
_PARTIAL: Final = ".part"


@dataclass(frozen=True, slots=True)
class ModelFile:
    """A model file: its name in the cache, where it comes from, its digest."""

    name: str
    url: str
    sha256: str


DETECTOR: Final = ModelFile(
    "face_detection_yunet_2023mar.onnx",
    f"{_ZOO}/f12e12798e8314f7c074a6656816c048dcc95b7a/models/face_detection_yunet/"
    "face_detection_yunet_2023mar.onnx",
    "8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
)
EMBEDDER: Final = ModelFile(
    "face_recognition_sface_2021dec.onnx",
    f"{_ZOO}/ba91a3b91d00d76e86540d4013f944bd6b514e39/models/face_recognition_sface/"
    "face_recognition_sface_2021dec.onnx",
    "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
)
# Downloads `url` into the file: the real one reads the network, a test's does not.
type Fetch = Callable[[str, Path], None]


def download(url: str, target: Path) -> None:
    """Save the file at an HTTPS URL.

    Args:
        url: The model's URL.
        target: Where to write it.

    Raises:
        ValueError: The URL is not HTTPS.
    """
    if not url.startswith("https://"):
        message = f"Not an HTTPS URL: {url}"
        raise ValueError(message)
    with (
        urllib.request.urlopen(url, timeout=_TIMEOUT) as answer,  # noqa: S310
        target.open("wb") as file,
    ):
        shutil.copyfileobj(answer, file, _CHUNK)


def ensure_model(models_dir: Path, model: ModelFile, fetch: Fetch = download) -> Path:
    """Return the model file, downloading it first when missing or altered.

    Args:
        models_dir: `models/` of the cache.
        model: Which file.
        fetch: How to download it.

    Returns:
        The file, its digest checked.

    Raises:
        FaceModelError: The download failed, or gave another file.
    """
    target = models_dir / model.name
    if target.is_file() and _digest(target) == model.sha256:
        return target
    partial = target.with_name(f"{model.name}{_PARTIAL}")
    try:
        models_dir.mkdir(parents=True, exist_ok=True)
        fetch(model.url, partial)
    except (OSError, ValueError) as exc:
        partial.unlink(missing_ok=True)
        raise FaceModelError(
            _("Cannot download the model {name}: {error}").format(
                name=model.name, error=exc
            ),
            _("Save {url} as {path} by hand, then run the command again.").format(
                url=model.url, path=target
            ),
        ) from exc
    if _digest(partial) != model.sha256:
        partial.unlink(missing_ok=True)
        raise FaceModelError(
            _("The model {name} downloaded is not the expected file.").format(
                name=model.name
            )
        )
    partial.replace(target)
    return target


def _digest(path: Path) -> str:
    """The SHA-256 of a file.

    Args:
        path: The file.

    Returns:
        Its digest in hexadecimal.
    """
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()
