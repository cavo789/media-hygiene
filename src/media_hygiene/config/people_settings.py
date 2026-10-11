"""`[people]` — the faces of `media-hygiene people`: which ones count, how close is one.

The faces are found once and kept in the cache with their size and sharpness: these
settings only choose which ones are grouped, so changing them costs no new analysis.
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.faces.cluster import SFACE_SIMILARITY

# Measured on sample faces (TODO 0058): below, the vector of a face drifts away from
# the same face seen sharp; to tune on a real collection.
MIN_FACE: Final = 40
MIN_SHARPNESS: Final = 30.0


class PeopleSettings(BaseModel):
    """`[people]` — the small and blurry faces left out, the grouping threshold."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Cosine similarity from which two faces may be the same person.
    similarity: float = Field(default=SFACE_SIMILARITY, gt=0, lt=1)
    # Faces whose box is smaller (shorter side, pixels) are not grouped.
    min_face: int = Field(default=MIN_FACE, ge=0)
    # Faces blurrier than this (variance of the Laplacian) are not grouped.
    min_sharpness: float = Field(default=MIN_SHARPNESS, ge=0)
