"""The models the bench compares: where their files come from, how they see a picture.

Every file is an ONNX export on Hugging Face, pinned to one revision, downloaded once
into the folder given on the command line and reused by the next runs. What was checked
about each licence, and where, is written next to the model (`licence`); "to check"
marks what could not be confirmed on the publisher's own page.

Sizes (Hugging Face API, read 2026-10-18): SigLIP 2 1,536 MB (vision 372, text 1,130,
tokenizer 34), CLIP 894 MB (vision 352, multilingual text 539, tokenizer 2, projection
1.6), DINOv2-small 89 MB: 2.5 GB in all.
"""

from __future__ import annotations

import shutil
import sys
import urllib.request
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from PIL import Image

if TYPE_CHECKING:
    from pathlib import Path

HUB: Final = "https://huggingface.co"
USER_AGENT: Final = "media-hygiene-embeddings-bench (TODO 0220)"
_TIMEOUT_SECONDS: Final = 60
_MEGABYTE: Final = 1_000_000
_PARTIAL: Final = ".part"

_SIGLIP: Final = (
    "onnx-community/siglip2-base-patch16-224-ONNX",
    "ba1f3b0843f24bc5417d38e19c37b287d719b2f4",
)
_CLIP: Final = (
    "Xenova/clip-vit-base-patch32",
    "d15189d7028b43f1d3e65039190477f6af591c2a",
)
_MCLIP: Final = (
    "sentence-transformers/clip-ViT-B-32-multilingual-v1",
    "58edf8cada9e398793dca955574a48cbb7f18be2",
)
_DINO: Final = (
    "onnx-community/dinov2-small",
    "8b1f705a3a7f6f062f6bdd21986c1583d3ef105d",
)

_HALF: Final = (0.5, 0.5, 0.5)
_CLIP_MEAN: Final = (0.48145466, 0.4578275, 0.40821073)
_CLIP_STD: Final = (0.26862954, 0.26130258, 0.27577711)
_IMAGENET_MEAN: Final = (0.485, 0.456, 0.406)
_IMAGENET_STD: Final = (0.229, 0.224, 0.225)
_SIDE: Final = 224


@dataclass(frozen=True, slots=True)
class Remote:
    """One file of a model on Hugging Face, at a pinned revision."""

    repo: str
    revision: str
    path: str

    @property
    def url(self) -> str:
        """Where to download it.

        Returns:
            The URL of the file at its revision.
        """
        return f"{HUB}/{self.repo}/resolve/{self.revision}/{self.path}"

    def local(self, root: Path) -> Path:
        """Where it is kept once downloaded.

        Args:
            root: The models folder.

        Returns:
            Its path below the folder: repository, then path in the repository.
        """
        return root / self.repo / self.path


@dataclass(frozen=True, slots=True)
class Pixels:
    """How a model wants its picture: size, crop and colour scale."""

    side: int  # the square the model reads
    shortest: int  # shortest edge before a centre crop; 0: squashed to the square
    mean: tuple[float, float, float]
    std: tuple[float, float, float]
    resample: Image.Resampling


@dataclass(frozen=True, slots=True)
class Words:  # pylint: disable=too-many-instance-attributes  # one per setting
    """How a model reads a search: its text model, tokenizer and pooling."""

    model: Remote
    tokenizer: Remote
    max_tokens: int
    pad_to: int = 0  # SigLIP reads exactly 64 tokens; 0: no padding
    end: str = ""  # a token to end the text with, when the tokenizer does not add it
    lowercase: bool = False
    output: str = "pooler_output"  # `last_hidden_state`: averaged, then `dense`
    dense: Remote | None = None  # a projection to the image space (safetensors)


@dataclass(frozen=True, slots=True)
class ModelSpec:
    """One model of the bench."""

    name: str
    title: str
    licence: str
    image: Remote
    image_output: str  # `last_hidden_state`: its first token (CLS)
    pixels: Pixels
    words: Words | None = None

    @property
    def remotes(self) -> tuple[Remote, ...]:
        """Every file the model needs.

        Returns:
            The image model, then the text side's files.
        """
        if self.words is None:
            return (self.image,)
        extra = () if self.words.dense is None else (self.words.dense,)
        return (self.image, self.words.model, self.words.tokenizer, *extra)


SIGLIP2: Final = ModelSpec(
    name="siglip2",
    title="SigLIP 2 base (multilingual)",
    licence=(
        "Apache-2.0 on Google's own card (google/siglip2-base-patch16-224, checked "
        "2026-10-18); the ONNX export (onnx-community) states none: to check"
    ),
    image=Remote(*_SIGLIP, "onnx/vision_model.onnx"),
    image_output="pooler_output",
    pixels=Pixels(_SIDE, 0, _HALF, _HALF, Image.Resampling.BILINEAR),
    words=Words(
        model=Remote(*_SIGLIP, "onnx/text_model.onnx"),
        tokenizer=Remote(*_SIGLIP, "tokenizer.json"),
        max_tokens=64,
        pad_to=64,
        end="<eos>",
        lowercase=True,
    ),
)
CLIP: Final = ModelSpec(
    name="clip",
    title="CLIP ViT-B/32 + multilingual text (clip-ViT-B-32-multilingual-v1)",
    licence=(
        "CLIP: MIT on OpenAI's GitHub repository (checked 2026-10-18), no licence on "
        "its Hugging Face card nor on the ONNX export (Xenova): to check; multilingual "
        "text: Apache-2.0 on its card (checked 2026-10-18)"
    ),
    image=Remote(*_CLIP, "onnx/vision_model.onnx"),
    image_output="image_embeds",
    pixels=Pixels(_SIDE, _SIDE, _CLIP_MEAN, _CLIP_STD, Image.Resampling.BICUBIC),
    words=Words(
        model=Remote(*_MCLIP, "onnx/model.onnx"),
        tokenizer=Remote(*_MCLIP, "tokenizer.json"),
        max_tokens=128,
        output="last_hidden_state",
        dense=Remote(*_MCLIP, "2_Dense/model.safetensors"),
    ),
)
DINOV2: Final = ModelSpec(
    name="dinov2",
    title="DINOv2 small (images only: near duplicates)",
    licence=(
        "Apache-2.0 on Meta's card (facebook/dinov2-small, checked 2026-10-18); the "
        "ONNX export (onnx-community) states none: to check"
    ),
    image=Remote(*_DINO, "onnx/model.onnx"),
    image_output="last_hidden_state",
    pixels=Pixels(_SIDE, 256, _IMAGENET_MEAN, _IMAGENET_STD, Image.Resampling.BICUBIC),
)
SPECS: Final = {spec.name: spec for spec in (SIGLIP2, CLIP, DINOV2)}


def fetch(remote: Remote, root: Path) -> Path:
    """Download a file once; a later run finds it in the models folder.

    Written beside its place first, then renamed: an interrupted download is never
    taken for a whole file.

    Args:
        remote: The file.
        root: The models folder.

    Returns:
        The local file.
    """
    target = remote.local(root)
    if target.is_file():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_name(target.name + _PARTIAL)
    sys.stdout.write(f"Downloading {remote.url}\n")
    request = urllib.request.Request(  # noqa: S310 - a fixed https URL of the hub
        remote.url, headers={"User-Agent": USER_AGENT}
    )
    opened = urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS)  # noqa: S310
    with opened as answer, partial.open("wb") as written:
        shutil.copyfileobj(answer, written)
    partial.replace(target)
    sys.stdout.write(f"  {target.stat().st_size / _MEGABYTE:.1f} MB\n")
    return target


def size_mb(spec: ModelSpec, root: Path) -> float:
    """Tell how much room a model's files take.

    Args:
        spec: The model.
        root: The models folder.

    Returns:
        Megabytes on disk, the files not downloaded yet counted as nothing.
    """
    files = (remote.local(root) for remote in spec.remotes)
    return sum(path.stat().st_size for path in files if path.is_file()) / _MEGABYTE
