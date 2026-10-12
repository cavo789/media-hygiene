"""The keys and variables this version knows, to name an unknown one and its twin."""

from __future__ import annotations

from difflib import get_close_matches
from typing import TYPE_CHECKING, Final, get_args

from pydantic import BaseModel

from media_hygiene.config.settings import Settings
from media_hygiene.constants import ENV_PREFIX

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

ENV_SEPARATOR: Final = "__"  # MEDIA_HYGIENE_<SECTION>__<KEY>


def model_in(annotation: object) -> type[BaseModel] | None:
    """Find the model a setting holds: itself, or the items of a tuple or union.

    Args:
        annotation: The type of a setting.

    Returns:
        The model, or None for a plain value.
    """
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    for argument in get_args(annotation):
        found = model_in(argument)
        if found is not None:
            return found
    return None


def fields_at(path: Sequence[str | int]) -> tuple[str, ...]:
    """List the keys known in a table of `config.toml`.

    Args:
        path: The table, e.g. `("general",)`; an index stands for one item of an
            array of tables (`("classify", "rules", 0)`).

    Returns:
        The key names, or none when the path leads to no table.
    """
    model: type[BaseModel] | None = Settings
    for part in path:
        if model is None:
            return ()
        if isinstance(part, int):
            continue
        field = model.model_fields.get(part)
        model = None if field is None else model_in(field.annotation)
    return () if model is None else tuple(model.model_fields)


def variable_name(section: str, key: str) -> str:
    """Name the environment variable of a setting.

    Args:
        section: TOML table, e.g. `general`.
        key: Key in the table, e.g. `locale`.

    Returns:
        E.g. `MEDIA_HYGIENE_GENERAL__LOCALE`.
    """
    return f"{ENV_PREFIX}{section}{ENV_SEPARATOR}{key}".upper()


def known_variables() -> tuple[str, ...]:
    """List every `MEDIA_HYGIENE_<SECTION>__<KEY>` this version reads.

    Returns:
        The variable names.
    """
    return tuple(
        variable_name(section, key)
        for section in fields_at(())
        for key in fields_at((section,))
    )


def unknown_variables(environ: Mapping[str, str]) -> tuple[str, ...]:
    """List the setting variables this version does not know (a typo, a newer key).

    Mount point variables (`MEDIA_HYGIENE_<NAME>_DIR`) have no double underscore
    and are left alone.

    Args:
        environ: The process environment.

    Returns:
        Their names, sorted.
    """
    known = set(known_variables())
    return tuple(
        name
        for name in sorted(environ)
        if name.startswith(ENV_PREFIX) and ENV_SEPARATOR in name and name not in known
    )


def closest(name: str, candidates: Iterable[str]) -> str | None:
    """Find the known name that looks most like a mistyped one.

    Args:
        name: The unknown key or variable.
        candidates: The names known at that place.

    Returns:
        The look-alike, or None when nothing is close.
    """
    matches = get_close_matches(name, list(candidates), n=1)
    return matches[0] if matches else None
