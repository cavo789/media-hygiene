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
from media_hygiene.report.decided_once import each_path_once

_FROZEN = ConfigDict(frozen=True, extra="forbid")


class UnwantedEntry(BaseModel):
    """One photo decided in `review --junk`, in host path, as the audit saw it."""

    model_config = _FROZEN

    path: str = Field(min_length=1)
    size: int = Field(ge=0)
    mtime_ns: int
    reason: UnwantedReason
    aside: bool = True


type UnwantedEntries = Annotated[
    tuple[UnwantedEntry, ...], AfterValidator(each_path_once)
]
