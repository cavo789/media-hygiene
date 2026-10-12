"""Turn what pydantic refused into sentences a user can act on, in their language."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.config.explain_many import Explained, explained, this_version
from media_hygiene.config.known_keys import (
    closest,
    fields_at,
    known_variables,
    variable_name,
)
from media_hygiene.config.origin import Origin, item_name, origin_in
from media_hygiene.config.reasons import reason
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _, ngettext
from media_hygiene.paths.docker_run import PUBLISHED_IMAGE

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from pydantic_core import ErrorDetails

    from media_hygiene.config.layers import Layer

_UNKNOWN: Final = "extra_forbidden"
_SETTING_DEPTH: Final = 2  # `section.key`: a whole variable, not a key inside one


@dataclass(frozen=True, slots=True)
class Problems:
    """What is wrong with the settings of a run."""

    errors: Sequence[ErrorDetails]
    layers: Mapping[Origin, Layer]
    variables: tuple[str, ...] = ()  # unknown `MEDIA_HYGIENE_<SECTION>__<KEY>`


def config_error(problems: Problems) -> ConfigError:
    """Explain every problem in one error; an unknown name says how to update.

    Args:
        problems: The refused values and unknown names.

    Returns:
        The error to raise, translated, without any pydantic wording.
    """
    found = [_unknown_variable(name) for name in problems.variables]
    found += [_sentence(error, problems.layers) for error in problems.errors]
    message = explained(found)
    unknown = bool(problems.variables) or any(
        error["type"] == _UNKNOWN for error in problems.errors
    )
    count = len(found)
    if not unknown:
        hint = ngettext(
            "Correct it, then run the same command again.",
            "Correct them, then run the same command again.",
            count,
        )
        return ConfigError(message, hint)
    hint = ngettext(
        "Correct or remove it, or update the image to the latest version:",
        "Correct or remove them, or update the image to the latest version:",
        count,
    )
    error = ConfigError(message, hint)
    error.command = f"docker pull {PUBLISHED_IMAGE}"
    return error


def _unknown_variable(name: str) -> Explained:
    """Explain an unknown setting variable.

    Args:
        name: E.g. `MEDIA_HYGIENE_GENERAL__TIMEZON`.

    Returns:
        The sentence, with the look-alike when there is one.
    """
    text = _(
        "The variable {name} is unknown to version {version}: a typo, or a "
        "setting of a newer version?"
    ).format(name=name, version=this_version())
    guess = closest(name, known_variables())
    place = _("The variable {name}").format(name=name)
    return Explained(True, _with_guess(text, guess), place, guess)  # noqa: FBT003


def _sentence(error: ErrorDetails, layers: Mapping[Origin, Layer]) -> Explained:
    """Explain one refused value or unknown key.

    Args:
        error: The pydantic error.
        layers: The raw layers, to tell a variable from a line of `config.toml`.

    Returns:
        The sentence, and the place for a bullet.
    """
    loc = error["loc"]
    why = reason(error)
    name = item_name(layers, loc)
    if name is not None and name.strip() in why:
        name = None  # the reason already names it (`rule 'Birthday': ...`)
    place = _place(loc, layers, name)
    if error["type"] != _UNKNOWN:
        refused = _("{place}: {reason}").format(place=place, reason=why)
        return Explained(False, f"{refused}.", refused)  # noqa: FBT003
    text = _(
        "{place} is unknown to version {version}: a typo, or a setting of a newer "
        "version?"
    ).format(place=place, version=this_version())
    guess = closest(str(loc[-1]), fields_at(loc[:-1]))
    return Explained(True, _with_guess(text, guess), place, guess)  # noqa: FBT003


def _with_guess(text: str, guess: str | None) -> str:
    """Add "did you mean" to a sentence when a known name looks alike.

    Args:
        text: The sentence.
        guess: The look-alike, if any.

    Returns:
        The sentence, completed.
    """
    if guess is None:
        return text
    return f"{text} {_("Did you mean '{key}'?").format(key=guess)}"


def _place(
    loc: Sequence[str | int], layers: Mapping[Origin, Layer], name: str | None
) -> str:
    """Say where a setting was written: a line of config.toml, a variable, an option.

    Args:
        loc: The pydantic location, e.g. `("general", "timezone")`.
        layers: The raw layers of the run.
        name: The `name` of the item of an array of tables, when it has one.

    Returns:
        E.g. `'timezone' in [general] of config.toml`.
    """
    if isinstance(loc[-1], int) and not fields_at(loc):
        loc = loc[:-1]  # an item of a plain list: the setting itself is named
    if len(loc) == 1 or isinstance(loc[-1], int):
        return _("{table} in config.toml").format(table=_table(loc, name))
    section, key = str(loc[0]), str(loc[-1])
    origin = origin_in(layers, section, str(loc[1]))
    if origin is Origin.CLI:
        return _("'{key}' on the command line").format(key=key)
    if origin is not Origin.ENV:
        table = _table(loc[:-1], name)
        return _("'{key}' in {table} of config.toml").format(key=key, table=table)
    name = variable_name(section, str(loc[1]))
    if len(loc) == _SETTING_DEPTH:
        return _("The variable {name}").format(name=name)
    return _("'{key}' in the variable {name}").format(key=key, name=name)


def _table(path: Sequence[str | int], name: str | None) -> str:
    """Name a table the way config.toml writes it.

    The number stays next to the name: two items may share a name, or the name
    may be the refused value.

    Args:
        path: E.g. `("general",)`, or `("classify", "rules", 0)` for the first rule.
        name: The `name` of the item, when it has one.

    Returns:
        E.g. `[general]`, `[[classify.rules]] number 1` or
        `[[classify.rules]] number 1 ('Birthday')`.
    """
    names = ".".join(part for part in path if isinstance(part, str))
    indexes = [part for part in path if isinstance(part, int)]
    if not indexes:
        return f"[{names}]"
    number = indexes[-1] + 1
    if name is None:
        return _("[[{table}]] number {number}").format(table=names, number=number)
    return _("[[{table}]] number {number} ('{name}')").format(
        table=names, number=number, name=name
    )
