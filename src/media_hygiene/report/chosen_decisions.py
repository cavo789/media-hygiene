r"""The `chosen` key of the decisions file: the files set aside in `search`.

```json
"chosen": [{"path": "C:\\Photos\\IMG_3.jpg", "size": 2048,
            "mtime_ns": 1700000000000000000, "found_by": "person:\"Ann\""}]
```

Each file is named by its host path and the version the index knew (size and
modification time): `clean --decisions` moves it to the quarantine only while it is
still that very file. `found_by` says which search found it, for the user's eyes.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

_FROZEN = ConfigDict(frozen=True, extra="forbid")


class ChosenFile(BaseModel):
    """One file set aside in `search`, in host path, as the index knew it."""

    model_config = _FROZEN

    path: str = Field(min_length=1)
    size: int = Field(ge=0)
    mtime_ns: int
    found_by: str = ""


def _each_file_once(files: tuple[ChosenFile, ...]) -> tuple[ChosenFile, ...]:
    """Refuse a file listed twice: which version is meant?

    Args:
        files: The files chosen.

    Returns:
        The files, unchanged.

    Raises:
        ValueError: A path appears twice.
    """
    paths = [file.path for file in files]
    if len(set(paths)) != len(paths):
        twice = sorted({path for path in paths if paths.count(path) > 1})
        message = f"{twice[0]} is chosen twice"
        raise ValueError(message)
    return files


type ChosenFiles = Annotated[tuple[ChosenFile, ...], AfterValidator(_each_file_once)]
