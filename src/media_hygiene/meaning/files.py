"""The files of the model in the cache: present, or downloaded once, said first.

They go into `models/` of the cache (never `/config`), next to the face models, and
are checked by their SHA-256 as those are. Nothing about the photos is sent: the
model runs on this computer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.faces.weights import MODELS_DIR_NAME, download, ensure_model
from media_hygiene.meaning.clip import DENSE, FILES, TEXT, TOKENIZER, VISION

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.faces.weights import Fetch


@dataclass(frozen=True, slots=True)
class ClipFiles:
    """The four files of the model, on disk."""

    vision: Path
    text: Path
    tokenizer: Path
    dense: Path


def models_dir(cache_dir: Path) -> Path:
    """Where the models are kept.

    Args:
        cache_dir: The `/cache` mount point.

    Returns:
        Its `models/` folder.
    """
    return cache_dir / MODELS_DIR_NAME


def clip_present(cache_dir: Path) -> bool:
    """Tell whether every file of the model is in the cache already.

    Args:
        cache_dir: The `/cache` mount point.

    Returns:
        True when nothing would be downloaded.
    """
    folder = models_dir(cache_dir)
    return all((folder / model.name).is_file() for model in FILES)


def clip_files(cache_dir: Path, fetch: Fetch = download) -> ClipFiles:
    """The files of the model, downloaded first when missing or altered.

    Args:
        cache_dir: The `/cache` mount point.
        fetch: How to download a file (the tests' writes no network).

    Returns:
        Their paths, digests checked.
    """
    folder = models_dir(cache_dir)
    vision, text, tokenizer, dense = (
        ensure_model(folder, model, fetch) for model in (VISION, TEXT, TOKENIZER, DENSE)
    )
    return ClipFiles(vision, text, tokenizer, dense)


def clip_known(cache_dir: Path) -> ClipFiles:
    """The paths the files have in the cache, without checking nor downloading them.

    Args:
        cache_dir: The `/cache` mount point.

    Returns:
        Their paths (`search` reads them as they are: it never downloads).
    """
    folder = models_dir(cache_dir)
    return ClipFiles(
        *(folder / model.name for model in (VISION, TEXT, TOKENIZER, DENSE))
    )
