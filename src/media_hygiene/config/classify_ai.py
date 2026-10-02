"""`[classify.ai]` — the local vision model a `subject` rule asks; off until set.

Nothing is sent anywhere unless a `subject` rule is written and `model` is set: the
tool sorts fully without a model. The pictures go to `url`, and only there.
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, Field

# Docker Desktop resolves this name; Docker Engine needs
# `--add-host=host.docker.internal:host-gateway`.
DEFAULT_URL: Final = "http://host.docker.internal:11434"
# Measured on a 27B vision model on one GPU (describe 3.5 s, map 0.9 s): the estimate
# until this machine has described a photo of its own.
SECONDS_PER_PHOTO: Final = 4.5


class AiSettings(BaseModel):
    """`[classify.ai]` — where the model is, how many photos it sees, how patiently.

    `model` empty: no photo is ever sent; a `subject` rule then stops the run.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    url: str = DEFAULT_URL
    model: str = ""
    map_model: str = ""  # text only; empty: `model`
    samples_per_event: int = Field(default=3, ge=1)
    min_edge: int = Field(default=512, ge=0)  # pixels, shorter side: tiny ones mislead
    image_edge: int = Field(default=768, ge=128)
    concurrency: int = Field(default=1, ge=1)  # one GPU: one photo at a time
    timeout_seconds: float = Field(default=180, gt=0)
    retries: int = Field(default=2, ge=0)
    batch_size: int = Field(default=20, ge=1)  # descriptions per mapping call
    confirm_above: int = Field(default=200, ge=0)
    seconds_per_photo: float = Field(default=SECONDS_PER_PHOTO, gt=0)

    @property
    def text_model(self) -> str:
        """The model that maps descriptions to categories.

        Returns:
            `map_model`, or `model` when empty.
        """
        return self.map_model or self.model
