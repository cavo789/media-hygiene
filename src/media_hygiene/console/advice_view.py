"""Print the advice a command closes with: safety lines, next step, best tips."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.markup import escape

from media_hygiene.console.advice import Advice, TipKind, select
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.console.output import Output


def print_advice(
    output: Output, drained: tuple[Advice | None, tuple[Advice, ...], tuple[str, ...]]
) -> None:
    """Print the safety lines, the 👉 line, the best tips and how many were left out.

    Args:
        output: Where to print.
        drained: The next step, the tips and the setting fragments collected.
    """
    step, tips, settings = drained
    setup = (
        Advice(
            TipKind.SETUP,
            _("To set once: {settings}.").format(
                settings="; ".join(escape(setting) for setting in settings)
            ),
        )
        if settings
        else None
    )
    selection = select(tips, setup, verbose=output.verbose)
    for advice in selection.safety:
        _print_tip(output, advice)
    if step is not None:
        output.console.print(f"👉 [bold]{_('What next:')}[/] {step.text}")
        if step.command is not None:
            output.command(step.command)
    for advice in selection.shown:
        _print_tip(output, advice)
    if selection.hidden:
        hidden = ngettext(
            "({count} more tip: add --verbosity verbose to see it.)",
            "({count} more tips: add --verbosity verbose to see them.)",
            selection.hidden,
        )
        output.console.print(f"[dim]{hidden.format(count=selection.hidden)}[/]")


def _print_tip(output: Output, advice: Advice) -> None:
    """Print one tip, with the command it suggests.

    Args:
        output: Where to print.
        advice: The tip.
    """
    if advice.kind is TipKind.SETUP:
        output.console.print(f"⚙️  [cyan]{advice.text}[/]")
    else:
        output.tip(advice.text)
    if advice.command is not None:
        output.command(advice.command)
