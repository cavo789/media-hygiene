"""What `classify` says of a `config.toml` written before the sort convention (0401).

A layout other than the convention's is offered `config --convention` (one tip, the
file never rewritten silently). A rule whose category holds several folder levels
(`Fêtes/Anniversaires/…`) does not fit `YYYY/YYYY-MM/<name>`: each one is named once,
with what to change, in one line.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape

from media_hygiene.cli.next_steps import carried
from media_hygiene.console.advice import Advice, TipKind
from media_hygiene.i18n import _, ngettext
from media_hygiene.services.config_convention import layout_changes
from media_hygiene.services.next_command import NextVerb, next_command

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

_LEVEL = "/"
_NAMED = 3  # the rules named in the one warning line


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
    deep = [
        rule.name
        for rule in runtime.settings.classify.rules
        if _LEVEL in rule.category.strip(_LEVEL)
    ]
    if deep:  # one line, however many rules
        named = ", ".join(f"'{escape(name)}'" for name in deep[:_NAMED])
        more = "…" if len(deep) > _NAMED else ""
        output.warning(
            ngettext(
                "{n} rule gives a category of several folder levels ({names}): "
                "the convention wants one name (2009/2009-11/<name>). Write one "
                "name in its category in config.toml (the rule itself still works).",
                "{n} rules give a category of several folder levels ({names}): "
                "the convention wants one name (2009/2009-11/<name>). Write one "
                "name in their category in config.toml (the rules themselves still "
                "work).",
                len(deep),
            ).format(n=len(deep), names=named + more)
        )
