"""The second question: which of a rule's categories each description belongs to.

Text only, several descriptions per call. The categories are listed with the user's
definitions; the answer is constrained to their names, or none.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.classify.ai.categories import offered
from media_hygiene.classify.ai.prompts import OPTIONS, loads, prompt
from media_hygiene.classify.ai.subjects import NONE

if TYPE_CHECKING:
    from collections.abc import Sequence

NONE_ANSWER: Final = "none"


def map_request(
    model: str, summaries: Sequence[str], categories: Sequence[str]
) -> dict[str, object]:
    """The question mapping descriptions to the categories of a rule.

    Args:
        model: The text model.
        summaries: The descriptions, in order.
        categories: The rule's categories, `Name = definition` or a name.

    Returns:
        The `/api/chat` body: one choice per description, from an `enum`.
    """
    numbered = "\n".join(f"{n}. {text}" for n, text in enumerate(summaries, 1))
    listed = [offered(entry) for entry in categories]
    content = prompt("map").format(
        categories="\n".join(category.line for category in listed),
        none=NONE_ANSWER,
        count=len(summaries),
        descriptions=numbered,
    )
    choices = {
        "type": "string",
        "enum": [*(category.name for category in listed), NONE_ANSWER],
    }
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
        "options": OPTIONS,
    }


def read_mapping(
    content: str, count: int, categories: Sequence[str]
) -> tuple[str, ...] | None:
    """Read the categories chosen for `count` descriptions.

    Args:
        content: The answer's text.
        count: How many descriptions were sent.
        categories: The rule's category names.

    Returns:
        One category per description (`NONE` when none fits), or None when the
        answer does not hold exactly one known choice per description.
    """
    value = loads(content)
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
