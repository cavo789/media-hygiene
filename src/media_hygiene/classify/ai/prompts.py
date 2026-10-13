"""The question about one photo, in the language of the interface, and its answer.

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

if TYPE_CHECKING:
    from media_hygiene.constants import Locale

_TEMPLATES: Final = Path(__file__).parent / "templates"
_VERSION_LENGTH: Final = 12
_MAX_TAGS: Final = 5
_DESCRIBE_TOKENS: Final = 160
OPTIONS: Final = {"temperature": 0}
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
        name: `describe_en`, `describe_fr`, `map`, ...

    Returns:
        Its text.
    """
    return (_TEMPLATES / f"{name}.txt").read_text(encoding="utf-8")


def version(name: str) -> str:
    """The version of a prompt: a digest of its text.

    Args:
        name: `describe_en`, `describe_fr`, `map`, ...

    Returns:
        A short hexadecimal digest.
    """
    return hashlib.sha256(prompt(name).encode()).hexdigest()[:_VERSION_LENGTH]


def describe_name(language: Locale) -> str:
    """The describe prompt in a language: its name is part of the cache identity.

    Args:
        language: The language of the interface.

    Returns:
        `describe_en` or `describe_fr`.
    """
    return f"describe_{language.value}"


def photo_chat(model: str, image: bytes, name: str) -> dict[str, object]:
    """The part of an `/api/chat` body every question about one photo shares.

    Args:
        model: The vision model.
        image: The photo, as JPEG.
        name: The prompt template.

    Returns:
        The model and the one user message, the photo attached.
    """
    picture = base64.b64encode(image).decode("ascii")
    message = {"role": "user", "content": prompt(name), "images": [picture]}
    return {"model": model, "messages": [message]}


def describe_request(
    model: str, image: bytes, name: str = "describe_en"
) -> dict[str, object]:
    """The question about one photo.

    Args:
        model: The vision model.
        image: The photo, as JPEG.
        name: The prompt, in the language of the answer.

    Returns:
        The `/api/chat` body.
    """
    return {
        **photo_chat(model, image, name),
        "format": DESCRIBE_SCHEMA,
        "think": False,
        "options": {**OPTIONS, "num_predict": _DESCRIBE_TOKENS},
    }


def read_description(content: str, seconds: float) -> Description | None:
    """Read the answer about one photo.

    Args:
        content: The answer's text.
        seconds: How long it took.

    Returns:
        The description, or None when the answer does not follow the schema.
    """
    value = loads(content)
    text = value.get("description") if isinstance(value, dict) else None
    if not isinstance(text, str) or not text.strip() or not isinstance(value, dict):
        return None
    tags = value.get("tags")
    found = [str(tag).strip() for tag in tags] if isinstance(tags, list) else []
    return Description(text.strip(), tuple(t for t in found if t)[:_MAX_TAGS], seconds)


def loads(content: str) -> object:
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
