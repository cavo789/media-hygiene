"""The question of 0589: which of the landmarks around does this photo show?

A short numbered list to pick from, never a free guess: an answer outside it is no
answer, and 0 says the photo shows none of them.
"""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.ai.prompts import OPTIONS, loads, prompt

if TYPE_CHECKING:
    from collections.abc import Sequence

PROMPT: Final = "landmark"
_TOKENS: Final = 16
_SCHEMA: Final = {
    "type": "object",
    "properties": {"choice": {"type": "integer"}},
    "required": ["choice"],
}


def landmark_request(
    model: str, image: bytes, candidates: Sequence[str]
) -> dict[str, object]:
    """The question about one photo and the landmarks around it.

    Args:
        model: The vision model.
        image: The photo, as JPEG.
        candidates: The landmarks around, nearest first.

    Returns:
        The `/api/chat` body.
    """
    listed = "\n".join(f"{rank}. {name}" for rank, name in enumerate(candidates, 1))
    picture = base64.b64encode(image).decode("ascii")
    message = {
        "role": "user",
        "content": f"{prompt(PROMPT)}{listed}",
        "images": [picture],
    }
    return {
        "model": model,
        "messages": [message],
        "format": _SCHEMA,
        "think": False,
        "options": {**OPTIONS, "num_predict": _TOKENS},
    }


def read_landmark(content: str, candidates: Sequence[str]) -> str | None:
    """Read the model's pick.

    Args:
        content: The answer's text.
        candidates: The list it was asked to pick from.

    Returns:
        The landmark picked, "" for none of them, None for an answer outside the list.
    """
    value = loads(content)
    choice = value.get("choice") if isinstance(value, dict) else None
    if isinstance(choice, bool) or not isinstance(choice, int):
        return None
    if choice == 0:
        return ""
    return candidates[choice - 1] if 0 < choice <= len(candidates) else None
