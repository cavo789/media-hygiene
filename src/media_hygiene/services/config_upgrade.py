"""`config --upgrade`: add the settings of this version to an existing `config.toml`.

The comments added are in the file's language (`general.locale`), whatever the
language of the run. The completed file must give the same effective settings as
before, or nothing is written; it is replaced atomically, then read back from the disk.
No backup is left in `/config`, which holds `config.toml` only: `--dry-run` shows what
would be added instead.
"""

from __future__ import annotations

import tomllib
from importlib.metadata import version as package_version
from typing import TYPE_CHECKING, Final

from media_hygiene.config.loader import default_config
from media_hygiene.config.settings import Settings
from media_hygiene.config.upgrade import Upgrade, plan_upgrade
from media_hygiene.constants import APP_NAME, Locale
from media_hygiene.errors import ConfigError, MountError
from media_hygiene.i18n import _, active_locale, using
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import is_read_only
from media_hygiene.text_files import read_user_text

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

_ENCODING: Final = "utf-8"


def config_upgrade(runtime: Runtime, *, dry_run: bool) -> Upgrade:
    """Complete `config.toml` with the settings it lacks, or say what it would add.

    Args:
        runtime: Settings, mount points and output.
        dry_run: Write nothing.

    Returns:
        What the file gains, its text read back from the disk once written.

    Raises:
        MountError: `/config` is not mounted, holds no file, or is read-only.
        ConfigError: The completed file would change a setting: nothing written.
    """
    config_file = _checked(runtime, dry_run=dry_run)
    text = read_user_text(config_file)
    upgrade = pending_upgrade(text)
    if not upgrade.added or dry_run:
        return upgrade
    if _effective(upgrade.text) != _effective(text):
        raise ConfigError(
            _("Completing {path} would change a setting: nothing was written.").format(
                path=runtime.mapper.to_host(config_file)
            )
        )
    temporary = config_file.with_name(f".{config_file.name}.tmp")
    temporary.write_text(upgrade.text, _ENCODING)
    temporary.replace(config_file)
    read_back = read_user_text(config_file)  # proof, not promise
    if pending_upgrade(read_back).added:
        raise ConfigError(
            _("{path} was written but is still incomplete.").format(
                path=runtime.mapper.to_host(config_file)
            )
        )
    return Upgrade(read_back, upgrade.added, upgrade.written_by)


def pending_upgrade(text: str) -> Upgrade:
    """What this version would add to a `config.toml`.

    Args:
        text: The file.

    Returns:
        The completed text and the settings it gains.
    """
    with using(_language_of(text)):
        template = default_config(_language_of(text))
    return plan_upgrade(text, template, package_version(APP_NAME))


def _checked(runtime: Runtime, *, dry_run: bool) -> Path:
    """The file to complete, refused when it cannot be.

    Args:
        runtime: Settings, mount points and output.
        dry_run: Only read it.

    Returns:
        `config.toml`.

    Raises:
        MountError: `/config` is not mounted, holds no file, or is read-only.
    """
    locations = runtime.locations
    config_file, folder = locations.config_file, locations.config_dir
    host = runtime.mapper.to_host(folder)
    if not runtime.persistent(MountKind.CONFIG):
        raise MountError(
            _("/config is not mounted: there is no config.toml to complete."),
            _('Mount your folder, e.g. -v "$HOME\\media-hygiene\\config:/config".'),
        )
    if not config_file.is_file():
        raise MountError(
            _("There is no config.toml in {folder} yet.").format(folder=host),
            _("Run any command once: it creates the file, complete and commented."),
        )
    if not dry_run and is_read_only(folder):
        raise MountError(
            _("{folder} is mounted read-only: config.toml cannot be completed.").format(
                folder=host
            ),
            _("Mount it without :ro for this command, or add --dry-run."),
        )
    return config_file


def _language_of(text: str) -> Locale:
    """The language a `config.toml` is written for.

    Args:
        text: The file.

    Returns:
        Its `general.locale`, else the language of this run.
    """
    general = tomllib.loads(text).get("general", {})
    try:
        return Locale(general.get("locale"))
    except ValueError:
        return active_locale()


def _effective(text: str) -> Settings:
    """The settings a file gives, before the environment and the command line.

    Args:
        text: The file.

    Returns:
        Them.
    """
    return Settings.model_validate(tomllib.loads(text))
