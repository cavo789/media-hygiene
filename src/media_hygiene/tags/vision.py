"""The question `tags` asks the vision model, and the tags read from its answer.

A French (or English) sentence and 5 to 10 tags (prompt C of the benchmark, TODO
0072), with the measured fixes: no relationship words, phrases kept whole, one line of
JSON. The answer is cached as it came (`descriptions`, its own prompt digest); the
tags are normalized each time they are derived, so that a new stop word needs no
model call.
"""

from __future__ import annotations

import json
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.ai.describe import Question
from media_hygiene.classify.ai.models import Description
from media_hygiene.classify.ai.prompts import photo_chat, version
from media_hygiene.tags.models import Tag, TagSource
from media_hygiene.tags.normalize import normalize

if TYPE_CHECKING:
    from media_hygiene.constants import Locale
    from media_hygiene.tags.normalize import WordRules

MAX_TAGS: Final = 10
_TOKENS: Final = 240  # measured: 94 output tokens (median) for prompt C
_OPTIONS: Final = {"temperature": 0, "num_predict": _TOKENS}
_SCHEMA: Final = {
    "type": "object",
    "properties": {
        "description": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}, "maxItems": MAX_TAGS},
    },
    "required": ["description", "tags"],
}


def prompt_name(language: Locale) -> str:
    """The template of the question, in the language of the tags.

    Args:
        language: The language of the tags.

    Returns:
        `tags_fr` or `tags_en`.
    """
    return f"tags_{language.value}"


def prompt_version(language: Locale) -> str:
    """The digest of the question: another prompt describes again.

    Args:
        language: The language of the tags.

    Returns:
        A short hexadecimal digest.
    """
    return version(prompt_name(language))


def tags_question(language: Locale) -> Question:
    """The question about one photo, and how its answer is read.

    Args:
        language: The language of the tags.

    Returns:
        The question.
    """
    return Question(partial(_request, prompt_name(language)), read_answer)


def read_answer(content: str, seconds: float) -> Description | None:
    """Read the answer about one photo, its tags as the model wrote them.

    Args:
        content: The answer's text.
        seconds: How long it took.

    Returns:
        The description, or None when the answer does not follow the schema.
    """
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict):
        return None
    text = value.get("description")
    if not isinstance(text, str) or not text.strip():
        return None
    found = value.get("tags")
    words = [str(word).strip() for word in found] if isinstance(found, list) else []
    tags = tuple(word for word in words if word)[:MAX_TAGS]
    return Description(text.strip(), tags, seconds)


def vision_tags(
    description: Description, rules: WordRules, model: str
) -> tuple[Tag, ...]:
    """The tags of what a model saw: its sentence whole, then its words normalized.

    Args:
        description: The cached answer.
        rules: Language and stop words.
        model: The model that answered.

    Returns:
        A `caption` tag, then the `vision` tags.
    """
    words = normalize(description.tags, rules)
    return (
        Tag(TagSource.CAPTION, description.text, model),
        *(Tag(TagSource.VISION, word, model) for word in words),
    )


def _request(name: str, model: str, image: bytes) -> dict[str, object]:
    """The `/api/chat` body about one photo.

    Args:
        name: The prompt template.
        model: The vision model.
        image: The photo, as JPEG.

    Returns:
        The body.
    """
    return {
        **photo_chat(model, image, name),
        "format": _SCHEMA,
        "think": False,
        "options": _OPTIONS,
    }
