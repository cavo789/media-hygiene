"""`[cache]` — what the cache folder (`/cache`) may keep besides the index."""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, Field

_PREVIEWS_MAX_GB: Final = 2.0
_BYTES_PER_GB: Final = 1024**3


class CacheSettings(BaseModel):
    """`[cache]` — the bound of the previews kept between runs."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    # Beyond it, the previews shown least recently are removed (made again if needed).
    previews_max_gb: float = Field(default=_PREVIEWS_MAX_GB, gt=0)

    @property
    def previews_max_bytes(self) -> int:
        """The bound of the previews, in bytes.

        Returns:
            It.
        """
        return int(self.previews_max_gb * _BYTES_PER_GB)
