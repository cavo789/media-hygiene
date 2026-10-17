r"""The `gone` key of the decisions file: the files gone that `review --gone` decided.

```json
"gone": [{"path": "C:\\Photos\\IMG_3.jpg", "size": 2048,
          "mtime_ns": 1700000000000000000, "deleted": true}]
```

Every file answered is listed: deleted on purpose (`deleted`), or moved elsewhere (a
disk not plugged in: forget it). Each one is named by its host path and the version
the index knew (size and modification time). `clean --decisions` writes a journal mark
per file deleted on purpose (`mark-gone`) and forgets the files of both answers.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from media_hygiene.report.decided_once import each_path_once

_FROZEN = ConfigDict(frozen=True, extra="forbid")


class GoneEntry(BaseModel):
    """One file gone, decided in `review --gone`, in host path."""

    model_config = _FROZEN

    path: str = Field(min_length=1)
    size: int = Field(ge=0)
    mtime_ns: int
    deleted: bool = True


type GoneEntries = Annotated[tuple[GoneEntry, ...], AfterValidator(each_path_once)]
