r"""The words a step's form gives: checked, then handed to `mh` in a one-shot file.

`mh home` runs with a terminal, so `mh` cannot read what the page prints. A step that
takes words (an album's name, a NAS folder) writes them into `.mh-step.json` of the
reports folder, the one tool folder `mh` reads on the host and the page writes (its
audit); the server then ends with `STEP_EXIT_BASE + FIELDS_STEP`. `mh` reads the file
once, removes it and runs its words, `Noël 2025` one of them (`mh_menu.ps1.j2`,
`mh.sh.j2`). Each value is refused with its reason: empty, a double quote, a control
character, a leading `-` (an option, not a value), or not of its field's form.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.menu_entry import FieldKind
from media_hygiene.i18n import _
from media_hygiene.services.next_command import LAUNCHER_FUNCTION

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.cli.menu_entry import Field, Step
    from media_hygiene.review.home_views import HomeState

STEP_FILE_NAME: Final = ".mh-step.json"
# `MEDIA_HYGIENE_LAUNCHER_STEPS` of an `mh` that also reads the one-shot file.
RELAY_FIELDS: Final = "2"
_CONTROL: Final = re.compile(r"[\x00-\x1f\x7f]")
_FOLDER: Final = re.compile(r"^(?:[A-Za-z]:\\|\\\\[^\\]+\\[^\\]+|/)")
_NUMBER: Final = re.compile(r"^[0-9]+$")


class FieldError(ValueError):
    """A value a form gave is refused: the message says which and why."""


def checked_words(step: Step, values: Mapping[str, str]) -> tuple[str, ...]:
    """The words of a step, each field's value checked.

    Args:
        step: The step, its fields in its command.
        values: What the form gave, by field name.

    Returns:
        The words, each value one of them.

    Raises:
        FieldError: A value missing or refused; its message is translated.
    """
    if not step.fields or step.planned:
        raise FieldError(_("This step takes no words."))
    checked = {
        field.name: _checked(field, values.get(field.name, "")) for field in step.fields
    }
    return step.words(checked)


def _checked(field: Field, value: str) -> str:
    """One value, refused with its reason.

    Args:
        field: Its field.
        value: What the form gave.

    Returns:
        The value, without its outer spaces.

    Raises:
        FieldError: Empty, a quote, a control character, a leading `-`, a bad form.
    """
    text = value.strip()
    refusals = (
        (not text, _("a value is needed")),
        ('"' in text, _("no double quote")),
        (bool(_CONTROL.search(text)), _("no control character")),
        (text.startswith("-"), _("it cannot start with '-'")),
        (
            field.kind is FieldKind.FOLDER and not _FOLDER.match(text),
            _("a folder as the Explorer shows it, e.g. {example}"),
        ),
        (
            field.kind is FieldKind.NUMBER and not _NUMBER.match(text),
            _("a number"),
        ),
        (not re.fullmatch(field.pattern, text), _("not accepted, e.g. {example}")),
    )
    reason = next((reason for refused, reason in refusals if refused), "")
    if reason:
        message = f"{field.label}: {reason.format(example=field.example)}"
        raise FieldError(message)
    return text


def write_step(folder: Path, words: tuple[str, ...]) -> Path:
    """Write the one-shot file `mh` runs after the page ends, one word per line.

    Args:
        folder: The reports folder.
        words: The command's words, without `mh`.

    Returns:
        The file.
    """
    target = folder / STEP_FILE_NAME
    text = json.dumps({"words": list(words)}, ensure_ascii=False, indent=0)
    target.write_text(text + "\n", encoding="utf-8")
    return target


def named_step(state: HomeState, name: str) -> tuple[int, str] | None:
    """The number and command of a step without fields, from its name (0310).

    A page that does not know `mh menu`'s numbers (the audit report) names the step.

    Args:
        state: The home page's state.
        name: The step's name, e.g. `review-near`.

    Returns:
        Its number and command; None when it takes fields or cannot run now.
    """
    action = state.action(name)
    if action is None or action.number is None or action.fields:
        return None
    return action.number, action.command


def shown(words: tuple[str, ...]) -> str:
    """The command as the user would type it, a value with a space quoted.

    Args:
        words: The command's words, without `mh`.

    Returns:
        E.g. `mh album "Noël 2025" --category Noël`.
    """
    quoted = (f'"{word}"' if " " in word or "\\" in word else word for word in words)
    return " ".join((LAUNCHER_FUNCTION, *quoted))
