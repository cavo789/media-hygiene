"""The two questions asked to the model: describe a photo, then map descriptions.

The prompts live in `templates/`; their version is a digest of their text, so that a
changed prompt describes again instead of trusting answers to another question.
Answers are short and follow a JSON schema: output tokens dominate the time.
"""

from __future__ import annotations

import base64
import hashlib
import json
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.ai.models import Description
from media_hygiene.classify.ai.subjects import NONE

if TYPE_CHECKING:
    from collections.abc import Sequence

_TEMPLATES: Final = Path(__file__).parent / "templates"
_VERSION_LENGTH: Final = 12
_MAX_TAGS: Final = 5
_DESCRIBE_TOKENS: Final = 160
NONE_ANSWER: Final = "none"
_OPTIONS: Final = {"temperature": 0}
DESCRIBE_SCHEMA: Final = {
    "type": "object",
    "properties": {
        "description": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["description", "tags"],
}


@cache
def prompt(name: str) -> str:
    """Read a prompt.

    Args:
        name: `describe` or `map`.

    Returns:
        Its text.
    """
    return (_TEMPLATES / f"{name}.txt").read_text(encoding="utf-8")


def version(name: str) -> str:
    """The version of a prompt: a digest of its text.

    Args:
        name: `describe` or `map`.

    Returns:
        A short hexadecimal digest.
    """
    return hashlib.sha256(prompt(name).encode()).hexdigest()[:_VERSION_LENGTH]


def describe_request(model: str, image: bytes) -> dict[str, object]:
    """The question about one photo.

    Args:
        model: The vision model.
        image: The photo, as JPEG.

    Returns:
        The `/api/chat` body.
    """
    picture = base64.b64encode(image).decode("ascii")
    message = {"role": "user", "content": prompt("describe"), "images": [picture]}
    return {
        "model": model,
        "messages": [message],
        "format": DESCRIBE_SCHEMA,
        "think": False,
        "options": {**_OPTIONS, "num_predict": _DESCRIBE_TOKENS},
    }


def read_description(content: str, seconds: float) -> Description | None:
    """Read the answer about one photo.

    Args:
        content: The answer's text.
        seconds: How long it took.

    Returns:
        The description, or None when the answer does not follow the schema.
    """
    value = _loads(content)
    text = value.get("description") if isinstance(value, dict) else None
    if not isinstance(text, str) or not text.strip() or not isinstance(value, dict):
        return None
    tags = value.get("tags")
    found = [str(tag).strip() for tag in tags] if isinstance(tags, list) else []
    return Description(text.strip(), tuple(t for t in found if t)[:_MAX_TAGS], seconds)


def map_request(
    model: str, summaries: Sequence[str], categories: Sequence[str]
) -> dict[str, object]:
    """The question mapping descriptions to the categories of a rule.

    Args:
        model: The text model.
        summaries: The descriptions, in order.
        categories: The rule's categories.

    Returns:
        The `/api/chat` body: one choice per description, from an `enum`.
    """
    numbered = "\n".join(f"{n}. {text}" for n, text in enumerate(summaries, 1))
    content = prompt("map").format(
        categories="\n".join(categories),
        none=NONE_ANSWER,
        count=len(summaries),
        descriptions=numbered,
    )
    choices = {"type": "string", "enum": [*categories, NONE_ANSWER]}
    count = len(summaries)
    schema = {
        "type": "object",
        "properties": {
            "categories": {
                "type": "array",
                "items": choices,
                "minItems": count,
                "maxItems": count,
            }
        },
        "required": ["categories"],
    }
    return {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "format": schema,
        "think": False,
        "options": _OPTIONS,
    }


def read_mapping(
    content: str, count: int, categories: Sequence[str]
) -> tuple[str, ...] | None:
    """Read the categories chosen for `count` descriptions.

    Args:
        content: The answer's text.
        count: How many descriptions were sent.
        categories: The rule's categories.

    Returns:
        One category per description (`NONE` when none fits), or None when the
        answer does not hold exactly one known choice per description.
    """
    value = _loads(content)
    chosen = value.get("categories") if isinstance(value, dict) else None
    if not isinstance(chosen, list) or len(chosen) != count:
        return None
    allowed = {category.casefold(): category for category in categories}
    answers: list[str] = []
    for choice in chosen:
        text = str(choice).strip().casefold()
        if text == NONE_ANSWER:
            answers.append(NONE)
        elif text in allowed:
            answers.append(allowed[text])
        else:
            return None
    return tuple(answers)


def _loads(content: str) -> object:
    """Parse JSON, tolerating nonsense.

    Args:
        content: The text.

    Returns:
        The value, or None.
    """
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None
