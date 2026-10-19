"""A message of `mh phone`, safe inside double quotes, its fields as shell variables."""

from __future__ import annotations

from media_hygiene.services.launcher_menu import shell_safe


def say(text: str, *fields: str) -> str:
    """Make a message safe, then put a shell variable in each field.

    Args:
        text: The translated message.
        *fields: The names of its fields, each shown by the variable of that name.

    Returns:
        The message for the script: `{count}` becomes `${count}`.
    """
    said = shell_safe(text)
    for name in fields:
        said = said.replace(f"{{{name}}}", f"${{{name}}}")
    return said
