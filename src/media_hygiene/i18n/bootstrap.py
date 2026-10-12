"""Pick the interface language before the CLI is built, so `--help` is translated."""

from __future__ import annotations

from os import environ
from typing import TYPE_CHECKING

from media_hygiene.config.layers import merge_layers, read_env_layer, read_file_layer
from media_hygiene.config.loader import load_settings
from media_hygiene.constants import Locale
from media_hygiene.errors import ConfigError
from media_hygiene.paths.locations import Locations

if TYPE_CHECKING:
    from collections.abc import Sequence

_LOCALE_FLAG = "--locale"


def locale_from_argv(argv: Sequence[str]) -> Locale | None:
    """Find a valid `--locale X` or `--locale=X` anywhere on the command line.

    Args:
        argv: Command-line arguments, without the program name.

    Returns:
        The requested locale, or None when absent or invalid (Typer reports it later).
    """
    for index, argument in enumerate(argv):
        value: str | None = None
        if argument == _LOCALE_FLAG and index + 1 < len(argv):
            value = argv[index + 1]
        elif argument.startswith(f"{_LOCALE_FLAG}="):
            value = argument.partition("=")[2]
        if value is not None and value in Locale:
            return Locale(value)
    return None


def resolve_locale(argv: Sequence[str]) -> Locale:
    """Resolve the language with the usual precedence: CLI, environment, file, default.

    Args:
        argv: Command-line arguments, without the program name.

    Returns:
        The locale to install. A refused config keeps the language it names, else
        falls back to English: the command itself reports the error right after.
    """
    from_cli = locale_from_argv(argv)
    if from_cli is not None:
        return from_cli
    locations = Locations()
    try:
        return load_settings(locations).settings.general.locale
    except ConfigError:
        return written_locale(locations)


def written_locale(locations: Locations) -> Locale:
    """Read the language alone from a configuration refused for another reason.

    A typo elsewhere in config.toml must not turn its error message to English.

    Args:
        locations: Mount points, giving the configuration file path.

    Returns:
        The locale written in the environment or the file when valid, else English.
    """
    try:
        layer = merge_layers(
            read_file_layer(locations.config_file), read_env_layer(environ)
        )
    except ConfigError:
        return Locale.EN
    value = layer.get("general", {}).get("locale")
    return Locale(value) if isinstance(value, str) and value in Locale else Locale.EN
