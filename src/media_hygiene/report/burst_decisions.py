r"""The `bursts` key of the decisions file: what `review` decided, series by series.

```json
"bursts": [{"status": "done", "kept": ["C:\\Photos\\IMG_1.jpg"],
            "discarded": ["C:\\Photos\\IMG_2.jpg"]}]
```

`review` lists every burst series from the start, `todo` until seen, then `done`; a
series kept whole has an empty `discarded`, a series set aside whole an empty `kept`.
Without `status` (older file, report), it is done.
"""

from __future__ import annotations

from collections import Counter
from enum import StrEnum
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, model_validator

_FROZEN = ConfigDict(frozen=True, extra="forbid")


class BurstStatus(StrEnum):
    """Whether a burst series was seen in the review."""

    TODO = "todo"  # listed when the review starts, every shot kept
    DONE = "done"


class BurstDecision(BaseModel):
    """The review of one burst series, in host paths.

    None may be set aside (the series was seen and kept whole, or not seen yet), or
    none kept (the whole series was set aside), but the series has at least one shot.
    """

    model_config = _FROZEN

    status: BurstStatus = BurstStatus.DONE
    kept: tuple[str, ...] = ()
    discarded: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _some_shot(self) -> BurstDecision:
        """Refuse a review without any shot, or a series not seen with shots aside.

        Returns:
            The review, unchanged.

        Raises:
            ValueError: Neither a kept nor a discarded shot, or a `todo` series with
                shots set aside.
        """
        if not self.kept and not self.discarded:
            message = "a reviewed burst series lists no shot"
            raise ValueError(message)
        if self.status is BurstStatus.TODO and self.discarded:
            message = "a burst series still to see has shots set aside"
            raise ValueError(message)
        return self


def _each_shot_once(
    bursts: tuple[BurstDecision, ...],
) -> tuple[BurstDecision, ...]:
    """Refuse a shot decided twice: kept or set aside?

    Args:
        bursts: The reviews of burst series.

    Returns:
        The reviews, unchanged.

    Raises:
        ValueError: A shot appears twice.
    """
    shots = Counter(
        shot for burst in bursts for shot in (*burst.kept, *burst.discarded)
    )
    twice = sorted(shot for shot, count in shots.items() if count > 1)
    if twice:
        message = f"{twice[0]} is decided twice"
        raise ValueError(message)
    return bursts


type BurstDecisions = Annotated[
    tuple[BurstDecision, ...], AfterValidator(_each_shot_once)
]
