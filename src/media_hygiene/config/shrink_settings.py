"""`[shrink]` — which videos `shrink` lightens, and how (0303).

A video is a candidate when its codec is one of `codecs` (old cameras: every frame a
JPEG, or a codec of the 2000s) or when it spends more than `bits_per_pixel` bits per
pixel and per frame (`bit_rate / (width * height * fps)`): a phone's H.264 spends
about 0.1 to 0.3, an MJPEG clip 0.5 to 2. It is re-encoded in H.264 (`libx264`):
`same_crf` keeps the picture (same size, visually the same), `lighter_crf` with at
most `lighter_lines` lines makes it lighter still, asked for with `--lighter`. A
result less than `min_gain_percent` percent smaller is thrown away and the video
remembered as not worth it. `preset`: x264's speed against size; `threads`: the
processors one encoding uses, 0 for half of them (the computer stays usable).
"""

from __future__ import annotations

from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field

CODECS: Final = (
    "mjpeg",
    "dvvideo",
    "mpeg4",
    "msmpeg4v1",
    "msmpeg4v2",
    "msmpeg4v3",
    "wmv1",
    "wmv2",
    "wmv3",
    "mpeg1video",
    "mpeg2video",
    "h263",
)
_BITS_PER_PIXEL: Final = 0.5
_MIN_GAIN_PERCENT: Final = 30
_SAME_CRF: Final = 18
_LIGHTER_CRF: Final = 23
_LIGHTER_LINES: Final = 720
_WORST_CRF: Final = 51  # x264's scale: 0 lossless, 51 the worst
_FEWEST_LINES: Final = 240
_MOST_LINES: Final = 4320  # 8K
_MOST_THREADS: Final = 256
type Preset = Literal[
    "ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower"
]


class ShrinkSettings(BaseModel):
    """`[shrink]` — the videos worth lightening, the quality kept, the gain required."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    codecs: tuple[str, ...] = CODECS
    bits_per_pixel: float = Field(default=_BITS_PER_PIXEL, gt=0)
    min_gain_percent: int = Field(default=_MIN_GAIN_PERCENT, ge=1, le=95)
    same_crf: int = Field(default=_SAME_CRF, ge=0, le=_WORST_CRF)
    lighter_crf: int = Field(default=_LIGHTER_CRF, ge=0, le=_WORST_CRF)
    lighter_lines: int = Field(default=_LIGHTER_LINES, ge=_FEWEST_LINES, le=_MOST_LINES)
    preset: Preset = "medium"
    threads: int = Field(default=0, ge=0, le=_MOST_THREADS)
