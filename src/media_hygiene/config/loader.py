"""Build the settings of a run: defaults < config.toml < environment < command line."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from importlib.metadata import version as package_version
from typing import TYPE_CHECKING

from pydantic import ValidationError

from media_hygiene.config.explain import Problems, config_error
from media_hygiene.config.known_keys import unknown_variables
from media_hygiene.config.layers import (
    Layer,
    merge_layers,
    read_env_layer,
    read_file_layer,
)
from media_hygiene.config.origin import Origin, origin_in
from media_hygiene.config.settings import Settings
from media_hygiene.constants import APP_NAME
from media_hygiene.i18n.templates import translated_environment

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.constants import Locale
    from media_hygiene.paths.locations import Locations

_TEMPLATE_PACKAGE = "media_hygiene.config"
_TEMPLATE_NAME = "config.toml.j2"


__all__ = [
    "LoadedSettings",
    "Origin",
    "default_config",
    "load_settings",
    "write_default_config",
]


@dataclass(frozen=True, slots=True)
class LoadedSettings:
    """Validated settings plus the raw layers they were merged from."""

    settings: Settings
    layers: dict[Origin, Layer] = field(default_factory=dict[Origin, Layer])

    def origin_of(self, section: str, key: str) -> Origin:
        """Tell which layer provided a setting.

        Args:
            section: TOML table, e.g. `general`.
            key: Key in the table, e.g. `locale`.

        Returns:
            One of the `Origin` values.
        """
        return origin_in(self.layers, section, key)


def load_settings(locations: Locations, cli: Layer | None = None) -> LoadedSettings:
    """Load and validate the settings of this run.

    Args:
        locations: Mount points, giving the configuration file path.
        cli: Overrides typed on the command line, by section.

    Returns:
        The validated settings and their layers.

    Raises:
        ConfigError: A value is invalid, or a key or variable unknown to this
            version; the message names it, in the user's language.
    """
    layers = {
        Origin.FILE: read_file_layer(locations.config_file),
        Origin.ENV: read_env_layer(os.environ),
        Origin.CLI: cli or {},
    }
    merged = merge_layers(layers[Origin.FILE], layers[Origin.ENV], layers[Origin.CLI])
    variables = unknown_variables(os.environ)
    try:
        settings = Settings.model_validate(merged)
    except ValidationError as exc:
        raise config_error(Problems(exc.errors(), layers, variables)) from exc
    if variables:
        raise config_error(Problems((), layers, variables))
    return LoadedSettings(settings, layers)


def default_config(locale: Locale) -> str:
    """The commented `config.toml` of this version, in the active language.

    Args:
        locale: The language stored in the file (`general.locale`).

    Returns:
        Its text, the version that wrote it on a comment line.
    """
    environment = translated_environment(_TEMPLATE_PACKAGE, escaped=())
    template = environment.get_template(_TEMPLATE_NAME)
    return template.render(locale=locale.value, version=package_version(APP_NAME))


def write_default_config(config_file: Path, locale: Locale) -> bool:
    """Create a commented `config.toml` when none exists yet.

    The comments are written in the active language, and `general.locale` is set to
    `locale`: a file created with `--locale fr` keeps the next runs in French.

    Args:
        config_file: Where the configuration file belongs.
        locale: The language of this run, stored in the file.

    Returns:
        True when the file was created.
    """
    if config_file.exists() or not config_file.parent.is_dir():
        return False
    text = default_config(locale)
    try:
        with config_file.open("x", encoding="utf-8") as stream:  # never over a file
            stream.write(text)
    except FileExistsError:
        return False
    return True
