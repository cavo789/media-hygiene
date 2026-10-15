"""What `mh` alone says around the menu: the prompt, a wrong number, the command learnt.

The `menu` command prints the steps; the `mh` function asks for the number and runs
the step itself (`services/launcher.py`). Its three messages are written into the
script, translated, with the shell variables they show (`$choice`, `$chosen`).
"""

from __future__ import annotations

from dataclasses import dataclass

from media_hygiene.i18n import _
from media_hygiene.services.next_command import LAUNCHER_FUNCTION

# Inside the double-quoted strings of both shells, these would be code, not text.
UNSAFE_CHARACTERS = frozenset('"$`\\')


@dataclass(frozen=True, slots=True)
class MenuTexts:
    """The messages of `mh` alone, ready to sit inside double quotes."""

    prompt: str
    unknown: str  # holds `$choice`
    direct: str  # holds `mh $chosen`


def menu_texts() -> MenuTexts:
    """Translate the messages of `mh` alone, the shell variables in place.

    Returns:
        The messages; a translation's quote or dollar sign is dropped, so that it
        cannot break the script.
    """
    return MenuTexts(
        prompt=_safe(_("Step number (Enter: the proposed one)")),
        unknown=_safe(
            _("No step {choice}: type mh alone to see the menu again.")
        ).replace("{choice}", "$choice"),
        direct=_safe(_("Next time, type it directly: {command}")).replace(
            "{command}", f"{LAUNCHER_FUNCTION} $chosen"
        ),
    )


def _safe(text: str) -> str:
    """Drop what a double-quoted string would read as code.

    Args:
        text: A translated message.

    Returns:
        The message without quotes, dollars, backticks nor backslashes.
    """
    return "".join(
        character for character in text if character not in UNSAFE_CHARACTERS
    )
