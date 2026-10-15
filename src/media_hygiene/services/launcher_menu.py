"""What `mh` says by itself: the menu's prompt, the command learnt, a folder not found.

The `menu` command prints the steps; the `mh` function asks for the number and runs
the step itself (`services/launcher.py`), after checking the photo folders. Its
messages are written into the script, translated, with the shell variables they show
(`$choice`, `$chosen`, `$folder`).
"""

from __future__ import annotations

from dataclasses import dataclass

from media_hygiene.i18n import _
from media_hygiene.services.next_command import LAUNCHER_FUNCTION

# Inside the double-quoted strings of both shells, these would be code, not text.
UNSAFE_CHARACTERS = frozenset('"$`\\')


@dataclass(frozen=True, slots=True)
class MenuTexts:
    """The messages of `mh` itself, ready to sit inside double quotes."""

    prompt: str
    unknown: str  # holds `$choice`
    direct: str  # holds `mh $chosen`
    missing: str  # holds `$folder`


def menu_texts() -> MenuTexts:
    """Translate the messages of `mh` itself, the shell variables in place.

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
        missing=_safe(
            _(
                "{folder} cannot be found: plug its disk in, or write mh again with "
                "launcher."
            )
        ).replace("{folder}", "$folder"),
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
