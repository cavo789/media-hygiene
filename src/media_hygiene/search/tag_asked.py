"""What the search page asks of `POST /api/hand-tag` (0555, 0546, 0622)."""

from __future__ import annotations

import re
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.config.hand_tags import LONGEST

MOST: Final = 20_000  # photos picked at once, as *Move to an event…*
MOST_WORDS: Final = 50  # tags dropped at once: the frequent list holds fewer
_CONTROL: Final = re.compile(r"[\x00-\x1f\x7f]")


class TagAsked(BaseModel):
    """The words there are, a word given or taken off, words dropped or merged."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Literal[
        "list",
        "add",
        "remove",
        "drop_look",
        "drop",
        "dropped",
        "restore",
        "frequent",
        "merge",
    ] = "list"
    keys: tuple[int, ...] = Field(default=(), max_length=MOST)
    word: str = Field(default="", max_length=LONGEST)
    words: tuple[str, ...] = Field(default=(), max_length=MOST_WORDS)  # 0622
    target: str = Field(default="", max_length=LONGEST)  # the tag a word means


def cleaned(word: str) -> str:
    """A word typed, without control characters nor extra spaces.

    Args:
        word: As sent.

    Returns:
        The word.
    """
    return " ".join(_CONTROL.sub(" ", word).split())
