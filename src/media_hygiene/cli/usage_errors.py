"""Command-line mistakes (an unknown option, a missing value) in the user's language.

Typer vendors Click without its gettext calls: its usage errors are English f-strings,
and the frame around them (the "Error" panel, "Try '…' for help.") English constants
read when Typer is imported. The localized classes hand every usage error to
`translated` before Typer prints it; `localize_error_frame` sets the frame's texts once
the locale is installed.
"""

from __future__ import annotations

import re
from typing import Final

from typer import rich_utils
from typer._click.exceptions import (
    BadParameter,
    MissingParameter,
    NoSuchOption,
    UsageError,
)

from media_hygiene.i18n import _

_INVALID: Final = re.compile(
    r"^Invalid value for (?P<hint>.+?): (?P<message>.*)$", re.DOTALL
)
_INVALID_ALONE: Final = re.compile(r"^Invalid value: (?P<message>.*)$", re.DOTALL)
_MISSING: Final = re.compile(
    r"^Missing (?P<kind>argument|option|parameter)(?P<hint> [^.]*)?\.(?P<rest>.*)$",
    re.DOTALL,
)
_EXTRA: Final = re.compile(
    r"^Got unexpected extra argument\(s\) \((?P<values>.*)\)$", re.DOTALL
)
_NOT_VALID: Final = re.compile(
    r"^(?P<value>.+) is not a valid (?P<kind>[a-z ]+)\.$", re.DOTALL
)
_NOT_IN_RANGE: Final = re.compile(
    r"^(?P<value>.+) is not in the range (?P<range>.+)\.$"
)
_NOT_ONE_OF: Final = re.compile(
    r"^(?P<value>.+) is not one of (?P<choices>.+)\.$", re.DOTALL
)
_NEEDS_ONE: Final = re.compile(r"^Option (?P<name>'.*?') requires an argument\.$")
_NEEDS_MORE: Final = re.compile(
    r"^Option (?P<name>'.*?') requires (?P<count>\d+) arguments\.$"
)
_TAKES_NONE: Final = re.compile(r"^Option (?P<name>'.*?') does not take a value\.$")
_COMMAND: Final = re.compile(
    r"^No such command (?P<name>'.*?')\.(?: Did you mean (?P<close>.*)\?)?$", re.DOTALL
)


def localize_error_frame() -> None:
    """Translate the texts Typer prints around a usage error: its title, its hint."""
    rich_utils.ERRORS_PANEL_TITLE = _("Error")
    rich_utils.RICH_HELP = _("Try [blue]'{command_path} {help_option}'[/] for help.")
    rich_utils.ABORTED_TEXT = _("Aborted.")


def translated(error: UsageError) -> UsageError:
    """The same usage error, its message in the language of the interface.

    Args:
        error: The error Click raised.

    Returns:
        A usage error with the translated message, the same context and exit code.
    """
    copy = UsageError(_message(error), error.ctx)
    copy.exit_code = error.exit_code
    return copy


def _message(error: UsageError) -> str:
    """Translate the message of a usage error, the parts Click knows.

    Args:
        error: The error.

    Returns:
        The message; a message of the tool itself is already translated.
    """
    if isinstance(error, NoSuchOption):
        text = _("No such option: {name}").format(name=error.option_name)
        if error.possibilities:
            options = ", ".join(sorted(error.possibilities))
            text += " " + _("(Possible options: {options})").format(options=options)
        return text
    message = error.format_message()
    if isinstance(error, MissingParameter) and (found := _MISSING.match(message)):
        kinds = {
            "argument": _("Missing argument"),
            "option": _("Missing option"),
            "parameter": _("Missing parameter"),
        }
        return f"{kinds[found['kind']]}{found['hint'] or ''}.{found['rest']}"
    if isinstance(error, BadParameter):
        return _bad_value(message)
    return _usage(message)


def _bad_value(message: str) -> str:
    """Translate the frame of an invalid value; the reason comes from the option.

    Args:
        message: Click's message.

    Returns:
        The translated message.
    """
    if found := _INVALID.match(message):
        text = _("Invalid value for {option}: {reason}")
        return text.format(option=found["hint"], reason=_reason(found["message"]))
    if found := _INVALID_ALONE.match(message):
        return _("Invalid value: {reason}").format(reason=_reason(found["message"]))
    return message


def _reason(reason: str) -> str:
    """Translate why a value was refused, when Click's own type said it.

    Args:
        reason: E.g. `'abc' is not a valid integer.`

    Returns:
        The reason translated; the tool's own reasons are already.
    """
    if found := _NOT_VALID.match(reason):
        numbers = any(word in found["kind"] for word in ("int", "float"))
        text = _("{value} is not a number.") if numbers else _("{value} is not valid.")
        return text.format(value=found["value"])
    if found := _NOT_IN_RANGE.match(reason):
        text = _("{value} is not in the range {range}.")
        return text.format(value=found["value"], range=found["range"])
    if found := _NOT_ONE_OF.match(reason):
        text = _("{value} is not one of {choices}.")
        return text.format(value=found["value"], choices=found["choices"])
    return reason


def _usage(message: str) -> str:
    """Translate the other usage errors: extra arguments, option values, commands.

    Args:
        message: Click's message.

    Returns:
        The translated message, or the message as it came.
    """
    if found := _EXTRA.match(message):
        text = _("Unexpected extra argument: {values}")
        return text.format(values=found["values"])
    if found := _NEEDS_ONE.match(message):
        return _("Option {name} needs a value.").format(name=found["name"])
    if found := _NEEDS_MORE.match(message):
        text = _("Option {name} needs {count} values.")
        return text.format(name=found["name"], count=found["count"])
    if found := _TAKES_NONE.match(message):
        return _("Option {name} takes no value.").format(name=found["name"])
    if found := _COMMAND.match(message):
        text = _("No such command {name}.").format(name=found["name"])
        if found["close"]:
            text += " " + _("Did you mean {names}?").format(names=found["close"])
        return text
    return message
