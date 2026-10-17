r"""The `unwanted` key of the decisions file: the photos `review --junk` decided.

```json
"unwanted": [{"path": "C:\\Photos\\IMG_3.jpg", "size": 2048,
              "mtime_ns": 1700000000000000000, "reason": "dark", "aside": true}]
```

Every photo the user decided is listed, set aside (`aside`) or kept: the review resumes
from them. Each one is named by its host path and the version the audit saw (size and
modification time): `clean --decisions` moves a photo set aside to the quarantine only
while it is still that very file.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from media_hygiene.plan.unwanted import UnwantedReason

_FROZEN = ConfigDict(frozen=True, extra="forbid")


class UnwantedEntry(BaseModel):
    """One photo decided in `review --junk`, in host path, as the audit saw it."""

    model_config = _FROZEN

    path: str = Field(min_length=1)
    size: int = Field(ge=0)
    mtime_ns: int
    reason: UnwantedReason
    aside: bool = True


def _each_photo_once(entries: tuple[UnwantedEntry, ...]) -> tuple[UnwantedEntry, ...]:
    """Refuse a photo listed twice: which decision would win?

    Args:
        entries: The photos decided.

    Returns:
        The photos, unchanged.

    Raises:
        ValueError: A path appears twice.
    """
    paths = [entry.path for entry in entries]
    if len(set(paths)) != len(paths):
        twice = sorted({path for path in paths if paths.count(path) > 1})
        message = f"{twice[0]} is decided twice"
        raise ValueError(message)
    return entries


type UnwantedEntries = Annotated[
    tuple[UnwantedEntry, ...], AfterValidator(_each_photo_once)
]
