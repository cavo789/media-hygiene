"""`[imports]` — what runs after an import, in order, each step on or off (0475).

`then` lists the steps run once the copies are done: `audit` (the new files join the
library), `tags` (🤖 the local model describes the new photos: skipped with one line
when it cannot be reached), `places` (🌐 the new spots named online, after their own
question, 0474). The audit always comes first while another step is on: tags and place
names read the index. An empty list: nothing runs after the copies.
The section is `[imports]`: `import` is a word of Python the settings cannot be named.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, field_validator


class ImportStep(StrEnum):
    """A step of the chain after an import, in the order they run."""

    AUDIT = "audit"
    TAGS = "tags"
    PLACES = "places"


class ImportSettings(BaseModel):
    """`[imports]` — the steps after an import."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    then: tuple[ImportStep, ...] = (
        ImportStep.AUDIT,
        ImportStep.TAGS,
        ImportStep.PLACES,
    )

    @field_validator("then")
    @classmethod
    def _audit_first(cls, steps: tuple[ImportStep, ...]) -> tuple[ImportStep, ...]:
        """Run each step once, in the chain's order, the audit first when needed.

        Args:
            steps: The steps as written.

        Returns:
            Them in order, `audit` added when another step is on.
        """
        chosen = set(steps)
        if chosen:
            chosen.add(ImportStep.AUDIT)
        return tuple(step for step in ImportStep if step in chosen)
