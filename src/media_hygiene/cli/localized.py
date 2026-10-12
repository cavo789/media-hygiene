"""Typer classes whose built-in help strings follow the interface language.

Typer vendors Click without its gettext calls: "Usage:" and the help of `--help` are
English literals. Click's public hooks (`format_usage`, `get_help_option`), reached
through Typer's `cls=`, translate them; nothing of Typer is patched. The root group
also turns Ctrl+C into one calm line instead of Typer's own abort.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from typer.core import TyperCommand, TyperGroup

from media_hygiene.cli.interrupted import stop_on_interrupt
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from typer._click import Command, Context, HelpFormatter
    from typer.core import TyperOption


def _write_usage(command: Command, ctx: Context, formatter: HelpFormatter) -> None:
    """Write the usage line of `command` behind a translated "Usage:".

    Args:
        command: The command whose usage is written.
        ctx: Context of the command.
        formatter: Help formatter receiving the line.
    """
    pieces = " ".join(command.collect_usage_pieces(ctx))
    formatter.write_usage(ctx.command_path, pieces, prefix=f"{_('Usage:')} ")


def _translate_help(option: TyperOption | None) -> TyperOption | None:
    """Translate the help text of the `--help` option.

    Args:
        option: The option Click built, None for a command without `--help`.

    Returns:
        The same option.
    """
    if option is not None:
        option.help = _("Show this message and exit.")
    return option


class LocalizedCommand(TyperCommand):
    """A command whose usage line and `--help` option are translated."""

    @override
    def format_usage(self, ctx: Context, formatter: HelpFormatter) -> None:
        """Write the usage line, translated.

        Args:
            ctx: Context of the command.
            formatter: Help formatter receiving the line.
        """
        _write_usage(self, ctx, formatter)

    @override
    def get_help_option(self, ctx: Context) -> TyperOption | None:
        """Return the `--help` option, its help text translated.

        Args:
            ctx: Context of the command.

        Returns:
            The option, None when the command has none.
        """
        return _translate_help(super().get_help_option(ctx))


class LocalizedGroup(TyperGroup):
    """The root group, translated like `LocalizedCommand`, calm on Ctrl+C."""

    @override
    def invoke(self, ctx: Context) -> Any:
        """Run the command; Ctrl+C ends it with one line, never a traceback.

        Args:
            ctx: Context of the group.

        Returns:
            What the command returned.
        """
        try:
            return super().invoke(ctx)
        except KeyboardInterrupt:
            stop_on_interrupt(ctx)

    @override
    def format_usage(self, ctx: Context, formatter: HelpFormatter) -> None:
        """Write the usage line, translated.

        Args:
            ctx: Context of the group.
            formatter: Help formatter receiving the line.
        """
        _write_usage(self, ctx, formatter)

    @override
    def get_help_option(self, ctx: Context) -> TyperOption | None:
        """Return the `--help` option, its help text translated.

        Args:
            ctx: Context of the group.

        Returns:
            The option, None when the group has none.
        """
        return _translate_help(super().get_help_option(ctx))
