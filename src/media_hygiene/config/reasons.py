"""Why pydantic refused a value, said in the user's language, not in its English."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from pydantic_core import ErrorDetails

_LIMITS: Final = ("ge", "gt", "le", "lt")  # the bound of a comparison error


def reason(error: ErrorDetails) -> str:
    """Explain why a value was refused.

    A validator of this project already raises a translated message; the common
    pydantic types get their own sentence; any other keeps pydantic's words.

    Args:
        error: The pydantic error.

    Returns:
        E.g. `a whole number is expected, not "abc"`.
    """
    context = error.get("ctx") or {}
    if error["type"] == "value_error" and "error" in context:
        return str(context["error"])
    template = _templates().get(error["type"])
    if template is None:
        return error["msg"]
    limit = next((context[key] for key in _LIMITS if key in context), "")
    expected = str(context.get("expected", "")).replace(" or ", ", ")
    return template.format(value=shown(error["input"]), limit=limit, expected=expected)


def shown(value: object) -> str:
    """Write a value the way it reads in config.toml.

    Args:
        value: The refused value.

    Returns:
        `true`/`false`, a quoted text, or the value as is.
    """
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, str):
        return f'"{value}"'
    return str(value)


def _templates() -> dict[str, str]:
    """Give the sentence of each common pydantic error type, translated now.

    Returns:
        The templates by error type; `{value}`, `{limit}` and `{expected}` are filled.
    """
    whole = _("a whole number is expected, not {value}")
    number = _("a number is expected, not {value}")
    boolean = _("true or false is expected, not {value}")
    choice = _("one of {expected} is expected, not {value}")
    return {
        "missing": _("this setting is required"),
        "int_parsing": whole,
        "int_type": whole,
        "int_from_float": whole,
        "float_parsing": number,
        "float_type": number,
        "bool_parsing": boolean,
        "bool_type": boolean,
        "string_type": _("a text between quotes is expected, not {value}"),
        "enum": choice,
        "literal_error": choice,
        "greater_than_equal": _("{limit} or more is expected, not {value}"),
        "greater_than": _("more than {limit} is expected, not {value}"),
        "less_than_equal": _("{limit} or less is expected, not {value}"),
        "less_than": _("less than {limit} is expected, not {value}"),
    }
