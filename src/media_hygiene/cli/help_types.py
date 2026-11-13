"""Plain words instead of Python types in the options column of `--help`.

Since 0.29, Typer prints each option's Python type (`<bool>`, `<list[str]>`) before its
help; a PowerShell user does not read `list[str]`, and the column wraps the help texts.
Typer shows an option's `metavar` instead when one is set (`display_type_rich`), so
every option without one gets a translated word here: nothing for a flag, `TEXT`,
`NUMBER`, `PATH` or the choices for a value. An argument's metavar is its name, so it
becomes a `PlainArgument` instead, whose type column uses the same words.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, get_args, override

from typer._click import Command
from typer.core import TyperArgument, TyperOption

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from typer._click import Context, Parameter
    from typer._coercion import TypeDescriptor

_NUMBERS = (int, float)


def _choice_word(choice: Any) -> str:  # noqa: ANN401 - Typer's choices are untyped
    """Name one choice as the user types it.

    Args:
        choice: A choice of the option, an enum member or a plain value.

    Returns:
        Its value as text.
    """
    return str(getattr(choice, "value", choice))


def value_word(descriptor: TypeDescriptor) -> str:
    """Name what an option's value is, in words the user reads.

    Args:
        descriptor: Typer's description of the option's annotation.

    Returns:
        The choices joined by `|`, or `PATH`, `NUMBER`, `TEXT`, translated.
    """
    if descriptor.choices:
        return "|".join(_choice_word(choice) for choice in descriptor.choices)
    if descriptor.is_path:
        return _("PATH")
    base = get_args(descriptor.annotation)[0] if descriptor.is_list else None
    if (base or descriptor.annotation) in _NUMBERS:
        return _("NUMBER")
    return _("TEXT")


class PlainArgument(TyperArgument):
    """A Typer argument whose type column reads a plain word."""

    @override
    def display_type_rich(self, ctx: Context) -> str | None:
        """Name the argument's value in plain words.

        Args:
            ctx: Context of the command.

        Returns:
            The word, as `value_word` gives it.
        """
        return value_word(self.type_descriptor)


def name_values(params: list[Parameter]) -> list[Parameter]:
    """Name each option's and argument's value in plain words; a flag shows none.

    Args:
        params: The parameters of a command.

    Returns:
        The same parameters.
    """
    for param in params:
        if isinstance(param, TyperOption) and param.metavar is None:
            param.metavar = "" if param.is_flag else value_word(param.type_descriptor)
        elif isinstance(param, TyperArgument) and not isinstance(param, PlainArgument):
            param.__class__ = PlainArgument
    return params


class PlainTypes(Command):  # pylint: disable=abstract-method  # a mixin
    """Mixin for a Typer command or group: its `--help` shows no Python type."""

    @override
    def get_params(self, ctx: Context) -> list[Parameter]:
        """Return the parameters, each option's value named in plain words.

        Args:
            ctx: Context of the command.

        Returns:
            The parameters, help option included.
        """
        return name_values(super().get_params(ctx))
