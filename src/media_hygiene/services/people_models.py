"""The face models of `people`: downloaded once into the cache, loaded by workers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.faces.weights import (
    DETECTOR,
    EMBEDDER,
    MODELS_DIR_NAME,
    ensure_model,
)
from media_hygiene.faces.worker import OnnxRecipe
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.faces.worker import FinderRecipe
    from media_hygiene.services.runtime import Runtime


def face_recipe(runtime: Runtime) -> FinderRecipe:
    """The models finding the faces, downloaded into the cache when missing.

    Args:
        runtime: Mount points.

    Returns:
        The recipe of the ONNX finder.
    """
    models = runtime.locations.cache_dir / MODELS_DIR_NAME
    if not all((models / model.name).is_file() for model in (DETECTOR, EMBEDDER)):
        runtime.output.info(
            _(
                "Downloading the two face models into the cache, once (39 MB): they "
                "run on this computer, nothing about your photos is sent."
            )
        )
    return OnnxRecipe(ensure_model(models, DETECTOR), ensure_model(models, EMBEDDER))
