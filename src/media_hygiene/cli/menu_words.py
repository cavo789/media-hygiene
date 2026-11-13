"""The words of a catalog step's command, its fields' values put in.

A field is a `{name}` word of the command, or an option (`--since`) added after it
when its value is not the field's default (0785: the period of a phone import).
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.cli.menu_entry import Step

_PLACEHOLDER: Final = re.compile(r"^\{(?P<name>\w+)\}$")


def command_words(step: Step, values: Mapping[str, str]) -> tuple[str, ...]:
    """The command's words, each `{field}` replaced by its value, kept whole.

    Args:
        step: The step, its command and fields.
        values: The value of each field, by name.

    Returns:
        The words, `Noël 2025` one of them; each option field's after them.
    """
    words = tuple(_word(word, values) for word in step.command.split())
    options = tuple(
        word
        for field in step.fields
        if field.option and values.get(field.name, field.example) != field.example
        for word in (field.option, values[field.name])
    )
    return words + options


def _word(word: str, values: Mapping[str, str]) -> str:
    """One word of a command, or the value its placeholder stands for.

    Args:
        word: The word, `{name}` for a field.
        values: The value of each field.

    Returns:
        The word or the value.
    """
    match = _PLACEHOLDER.match(word)
    return values[match["name"]] if match else word
