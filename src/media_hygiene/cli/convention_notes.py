"""What `classify` says of a `config.toml` written before the sort convention (0401).

A layout other than the convention's is offered `config --convention` (one tip, the
file never rewritten silently). A rule whose category holds several folder levels
(`Fêtes/Anniversaires/…`) does not fit `YYYY/YYYY-MM/<name>`: each one is named once,
with what to change.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape

from media_hygiene.cli.next_steps import carried
from media_hygiene.console.advice import Advice, TipKind
from media_hygiene.i18n import _
from media_hygiene.services.config_convention import layout_changes
from media_hygiene.services.next_command import NextVerb, next_command

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

_LEVEL = "/"


def note_convention(runtime: Runtime) -> None:
    """Offer the convention's layouts, and name the rules of several folder levels.

    Args:
        runtime: Settings, mount points and output.
    """
    output = runtime.output
    try:
        changes = layout_changes(runtime.locations.config_file)
    except OSError, ValueError:
        changes = ()  # the settings were loaded: a file read again fails only by a race
    if changes:
        command = next_command(
            runtime, NextVerb(carried(runtime, "config --convention"))
        )
        output.advise(
            Advice(
                TipKind.NEXT,
                _(
                    "Your config.toml sorts otherwise than the convention "
                    "year/year-month/event (2009/2009-11/Tom's birthday): this shows "
                    "the change and asks before writing it:"
                ),
                command.command,
            )
        )
    for rule in runtime.settings.classify.rules:  # several folder levels
        if _LEVEL in rule.category.strip(_LEVEL):
            output.warning(
                _(
                    "The rule '{name}' gives the category '{category}', several "
                    "folder levels: the convention wants one name "
                    "(2009/2009-11/<name>). Write one name in its category in "
                    "config.toml."
                ).format(name=escape(rule.name), category=escape(rule.category))
            )
