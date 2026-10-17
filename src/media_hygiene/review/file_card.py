"""A file as a review page shows it: name, folder, a line of details, a preview."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FileCard(BaseModel):
    """What every review page shows of a file; `preview` is empty when none is kept."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    folder: str
    details: str
    preview: str
