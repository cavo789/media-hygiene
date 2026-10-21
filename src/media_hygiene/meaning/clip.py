"""The model of search by meaning: CLIP ViT-B/32 and its multilingual text model.

Chosen by the maintainer on 2026-10-20 (TODO 0221, measured on 1,000 of their photos:
67 % of the first 5 pictures relevant on 20 French searches, 0.057 s per photo on 4
CPU threads). Four files, pinned to one revision of Hugging Face and checked by their
SHA-256, downloaded once into the cache (`ATTRIBUTION.txt` says where they come from
and under which licence): the image model, the text model, its tokenizer, and the
projection of its sentences into the space of the pictures.
"""

from __future__ import annotations

from typing import Final

from PIL import Image

from media_hygiene.faces.weights import ModelFile
from media_hygiene.meaning.pixels import Pixels

# Stored with each vector: a vector of another model is never compared.
MODEL: Final = "clip-vit-b32+multilingual-v1"
DIMENSIONS: Final = 512
_HUB: Final = "https://huggingface.co"
_IMAGES: Final = (
    f"{_HUB}/Xenova/clip-vit-base-patch32/resolve/"
    "d15189d7028b43f1d3e65039190477f6af591c2a"
)
_WORDS: Final = (
    f"{_HUB}/sentence-transformers/clip-ViT-B-32-multilingual-v1/resolve/"
    "58edf8cada9e398793dca955574a48cbb7f18be2"
)
VISION: Final = ModelFile(
    "clip-vit-b32-vision.onnx",
    f"{_IMAGES}/onnx/vision_model.onnx",
    "fd6e1402a588279d1723c7534d4bcba5bc0b14b47dfab0e46f8c47b8270d7d40",
)
TEXT: Final = ModelFile(
    "clip-multilingual-v1-text.onnx",
    f"{_WORDS}/onnx/model.onnx",
    "ca09969eb6e0f36fb1622654d1b47ac2025f576794f48b249a50b78d4b70373f",
)
TOKENIZER: Final = ModelFile(
    "clip-multilingual-v1-tokenizer.json",
    f"{_WORDS}/tokenizer.json",
    "5b4e1a8171c81dfd666ae40265b9530c6e0b3d53923fe8ac493dcc84229adf81",
)
DENSE: Final = ModelFile(
    "clip-multilingual-v1-dense.safetensors",
    f"{_WORDS}/2_Dense/model.safetensors",
    "d12568dc7300970a4d3dbb49068ad16cd89b99840b74b026f8e48071e9414f74",
)
FILES: Final = (VISION, TEXT, TOKENIZER, DENSE)
# Their sizes on Hugging Face (API, read 2026-10-20): 351.7 + 539.0 + 2.0 + 1.6 MB.
DOWNLOAD_MB: Final = 894
IMAGE_OUTPUT: Final = "image_embeds"
TEXT_OUTPUT: Final = "last_hidden_state"  # averaged over the tokens, then projected
MAX_TOKENS: Final = 128
_CLIP_MEAN: Final = (0.48145466, 0.4578275, 0.40821073)
_CLIP_STD: Final = (0.26862954, 0.26130258, 0.27577711)
_SIDE: Final = 224
PIXELS: Final = Pixels(_SIDE, _SIDE, _CLIP_MEAN, _CLIP_STD, Image.Resampling.BICUBIC)
# Measured by 0221 on the maintainer's PC (4 threads, decoding included): what a
# first run announces before it has timed a photo of its own.
SECONDS_PER_PHOTO: Final = 0.057
