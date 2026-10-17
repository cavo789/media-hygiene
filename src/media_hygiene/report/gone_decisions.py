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

_FROZEN = ConfigDict(frozen=True, extra="forbid")


class GoneEntry(BaseModel):
    """One file gone, decided in `review --gone`, in host path."""

    model_config = _FROZEN

    path: str = Field(min_length=1)
    size: int = Field(ge=0)
    mtime_ns: int
    deleted: bool = True


def _each_file_once(entries: tuple[GoneEntry, ...]) -> tuple[GoneEntry, ...]:
    """Refuse a file listed twice: which answer would win?

    Args:
        entries: The files decided.

    Returns:
        The files, unchanged.

    Raises:
        ValueError: A path appears twice.
    """
    paths = [entry.path for entry in entries]
    if len(set(paths)) != len(paths):
        twice = sorted({path for path in paths if paths.count(path) > 1})
        message = f"{twice[0]} is decided twice"
        raise ValueError(message)
    return entries


type GoneEntries = Annotated[tuple[GoneEntry, ...], AfterValidator(_each_file_once)]
